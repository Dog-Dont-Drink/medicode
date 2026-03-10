args <- commandArgs(trailingOnly = TRUE)
train_csv <- args[1]
test_csv <- args[2]
output_train_csv <- args[3]
output_test_csv <- args[4]
output_json <- args[5]
plot_path <- args[6]
plot_pdf_path <- args[7]
dataset_name <- args[8]
template_kind <- args[9]
outcome <- args[10]
time_var <- args[11]
event_var <- args[12]
target <- args[13]
knots_count <- as.integer(args[14])

options(repos = c(CRAN = Sys.getenv("MEDICODE_R_PACKAGE_REPO", unset = "https://cloud.r-project.org")))
auto_install_enabled <- tolower(Sys.getenv("MEDICODE_R_AUTO_INSTALL_ENABLED", unset = "true")) %in% c("1", "true", "yes")
ensure_package <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (!isTRUE(auto_install_enabled)) {
      stop(paste0("Missing R package: ", pkg), call. = FALSE)
    }
    install.packages(pkg, repos = getOption("repos")[["CRAN"]])
  }
}

script_dir <- dirname(normalizePath(sub("^--file=", "", commandArgs(FALSE)[grep("^--file=", commandArgs(FALSE))][1])))
source(file.path(script_dir, "ml_model_common.R"))

ensure_package("jsonlite")
ensure_package("ggplot2")
ensure_package("Hmisc")
ensure_package("survival")
library(jsonlite)
library(ggplot2)
suppressPackageStartupMessages(library(survival))

train_df <- read.csv(train_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
train_df <- trim_dataframe_strings(train_df)
has_test <- FALSE
test_df <- NULL
if (nzchar(test_csv) && test_csv != "NA" && file.exists(test_csv)) {
  raw_test <- read.csv(test_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  raw_test <- trim_dataframe_strings(raw_test)
  if (nrow(raw_test) > 0) {
    test_df <- raw_test
    has_test <- TRUE
  }
}

required_columns <- unique(c(target, outcome, time_var, event_var))
required_columns <- required_columns[required_columns != "NA" & nzchar(required_columns)]
missing_cols <- setdiff(required_columns, names(train_df))
if (length(missing_cols) > 0) {
  stop(paste0("Training set missing columns: ", paste(missing_cols, collapse = ", ")), call. = FALSE)
}

train_df <- train_df[stats::complete.cases(train_df[, required_columns, drop = FALSE]), , drop = FALSE]
if (nrow(train_df) < 20) {
  stop("RCS transform needs at least 20 complete observations.", call. = FALSE)
}

target_numeric <- suppressWarnings(as.numeric(train_df[[target]]))
if (all(is.na(target_numeric))) {
  stop("Target variable must be numeric.", call. = FALSE)
}
train_df[[target]] <- target_numeric
unique_target <- unique(target_numeric[!is.na(target_numeric)])
if (length(unique_target) < knots_count) {
  stop("Target variable has insufficient unique values for the requested knot count.", call. = FALSE)
}

knots_values <- Hmisc::rcspline.eval(train_df[[target]], nk = knots_count, knots.only = TRUE)
basis_train <- Hmisc::rcspline.eval(train_df[[target]], knots = knots_values, inclx = TRUE)
colnames(basis_train) <- paste0(target, "_rcs", seq_len(ncol(basis_train)))

output_train <- cbind(train_df, basis_train)

output_test <- NULL
if (has_test) {
  if (!target %in% names(test_df)) {
    has_test <- FALSE
  } else {
    test_df[[target]] <- suppressWarnings(as.numeric(test_df[[target]]))
    test_df <- test_df[stats::complete.cases(test_df[, required_columns[required_columns %in% names(test_df)], drop = FALSE]), , drop = FALSE]
    if (nrow(test_df) < 5) {
      has_test <- FALSE
    } else {
      basis_test <- Hmisc::rcspline.eval(test_df[[target]], knots = knots_values, inclx = TRUE)
      colnames(basis_test) <- paste0(target, "_rcs", seq_len(ncol(basis_test)))
      output_test <- cbind(test_df, basis_test)
    }
  }
}

effect_df <- data.frame()
p_overall <- NA_real_
p_nonlinear <- NA_real_
note <- ""

if (template_kind == "binary") {
  outcome_info <- prepare_binary_outcome(output_train, outcome)
  output_train <- outcome_info$data
  y <- outcome_info$outcome_numeric

  model_cols <- colnames(basis_train)
  formula_spline <- stats::as.formula(paste("y ~", paste(model_cols, collapse = " + ")))
  fit_spline <- stats::glm(formula_spline, data = output_train, family = stats::binomial())
  fit_null <- stats::glm(y ~ 1, data = output_train, family = stats::binomial())
  fit_linear <- stats::glm(y ~ output_train[[target]], data = output_train, family = stats::binomial())

  p_overall <- tryCatch(as.numeric(stats::anova(fit_null, fit_spline, test = "LRT")$`Pr(>Chi)`[2]), error = function(e) NA_real_)
  p_nonlinear <- tryCatch(as.numeric(stats::anova(fit_linear, fit_spline, test = "LRT")$`Pr(>Chi)`[2]), error = function(e) NA_real_)

  x_seq <- seq(stats::quantile(output_train[[target]], 0.01, na.rm = TRUE), stats::quantile(output_train[[target]], 0.99, na.rm = TRUE), length.out = 200)
  basis_seq <- Hmisc::rcspline.eval(x_seq, knots = knots_values, inclx = TRUE)
  colnames(basis_seq) <- model_cols
  newdata <- as.data.frame(basis_seq)

  pred <- stats::predict(fit_spline, newdata = newdata, type = "link", se.fit = TRUE)
  ref_x <- stats::median(output_train[[target]], na.rm = TRUE)
  ref_basis <- Hmisc::rcspline.eval(ref_x, knots = knots_values, inclx = TRUE)
  colnames(ref_basis) <- model_cols
  ref_eta <- as.numeric(stats::predict(fit_spline, newdata = as.data.frame(ref_basis), type = "link"))

  eta <- as.numeric(pred$fit)
  se <- as.numeric(pred$se.fit)
  or <- exp(eta - ref_eta)
  lower <- exp((eta - 1.96 * se) - ref_eta)
  upper <- exp((eta + 1.96 * se) - ref_eta)
  effect_df <- data.frame(x = x_seq, estimate = or, lower = lower, upper = upper)
  note <- "Restricted cubic spline effect estimated by logistic regression."
} else if (template_kind == "survival") {
  if (!nzchar(time_var) || !nzchar(event_var) || time_var == "NA" || event_var == "NA") {
    stop("Survival template requires time and event variables.", call. = FALSE)
  }
  event_info <- prepare_survival_event(output_train, event_var)
  output_train <- event_info$data
  event_numeric <- event_info$event_numeric
  time_numeric <- suppressWarnings(as.numeric(output_train[[time_var]]))
  if (all(is.na(time_numeric))) {
    stop("Time variable must be numeric for Cox model.", call. = FALSE)
  }
  output_train[[time_var]] <- time_numeric

  model_cols <- colnames(basis_train)
  formula_spline <- stats::as.formula(paste("survival::Surv(", backtick(time_var), ", event_numeric) ~", paste(model_cols, collapse = " + ")))
  fit_spline <- survival::coxph(formula_spline, data = output_train, ties = "efron", x = TRUE)
  fit_null <- survival::coxph(stats::as.formula(paste("survival::Surv(", backtick(time_var), ", event_numeric) ~ 1")), data = output_train, ties = "efron", x = TRUE)
  fit_linear <- survival::coxph(stats::as.formula(paste("survival::Surv(", backtick(time_var), ", event_numeric) ~", backtick(target))), data = output_train, ties = "efron", x = TRUE)

  p_overall <- tryCatch(as.numeric(stats::anova(fit_null, fit_spline, test = "Chisq")$`Pr(>|Chi|)`[2]), error = function(e) NA_real_)
  p_nonlinear <- tryCatch(as.numeric(stats::anova(fit_linear, fit_spline, test = "Chisq")$`Pr(>|Chi|)`[2]), error = function(e) NA_real_)

  x_seq <- seq(stats::quantile(output_train[[target]], 0.01, na.rm = TRUE), stats::quantile(output_train[[target]], 0.99, na.rm = TRUE), length.out = 200)
  basis_seq <- Hmisc::rcspline.eval(x_seq, knots = knots_values, inclx = TRUE)
  colnames(basis_seq) <- model_cols
  newdata <- as.data.frame(basis_seq)

  pred <- stats::predict(fit_spline, newdata = newdata, type = "lp", se.fit = TRUE)
  ref_x <- stats::median(output_train[[target]], na.rm = TRUE)
  ref_basis <- Hmisc::rcspline.eval(ref_x, knots = knots_values, inclx = TRUE)
  colnames(ref_basis) <- model_cols
  ref_eta <- as.numeric(stats::predict(fit_spline, newdata = as.data.frame(ref_basis), type = "lp"))

  eta <- as.numeric(pred$fit)
  se <- as.numeric(pred$se.fit)
  hr <- exp(eta - ref_eta)
  lower <- exp((eta - 1.96 * se) - ref_eta)
  upper <- exp((eta + 1.96 * se) - ref_eta)
  effect_df <- data.frame(x = x_seq, estimate = hr, lower = lower, upper = upper)
  note <- "Restricted cubic spline effect estimated by Cox regression."
} else {
  stop("Unsupported template kind.", call. = FALSE)
}

format_p_value <- function(p) {
  if (is.na(p)) {
    return("NA")
  }
  if (p < 0.001) {
    return("<0.001")
  }
  sprintf("%.3f", p)
}

subtitle_text <- paste0(
  "P-overall = ", format_p_value(p_overall),
  "; P-nonlinear = ", format_p_value(p_nonlinear)
)

plot_obj <- ggplot(effect_df, aes(x = x, y = estimate)) +
  geom_ribbon(aes(ymin = lower, ymax = upper), fill = "#10b981", alpha = 0.18) +
  geom_line(color = "#0f766e", linewidth = 1.15) +
  geom_hline(yintercept = 1, linetype = "dashed", color = "#94a3b8", linewidth = 0.8) +
  labs(
    title = "Restricted Cubic Spline Effect",
    subtitle = subtitle_text,
    x = "Predictor value",
    y = if (template_kind == "survival") "Hazard Ratio (ref=median)" else "Odds Ratio (ref=median)"
  ) +
  theme_bw(base_size = 10) +
  theme(
    panel.grid.minor = element_blank(),
    plot.title = element_text(face = "bold", size = 11),
    plot.subtitle = element_text(size = 9, color = "#475569")
  )

png(filename = plot_path, width = 1800, height = 1400, res = 300)
tryCatch({
  print(plot_obj)
}, finally = {
  dev.off()
})
ggsave(plot_pdf_path, plot_obj, width = 6, height = 4.8, device = cairo_pdf)

write.csv(output_train, output_train_csv, row.names = FALSE, fileEncoding = "UTF-8")
if (has_test && !is.null(output_test)) {
  write.csv(output_test, output_test_csv, row.names = FALSE, fileEncoding = "UTF-8")
}

result <- list(
  dataset_name = dataset_name,
  template_kind = template_kind,
  target = target,
  knots_count = knots_count,
  knots_values = as.numeric(knots_values),
  basis_columns = colnames(basis_train),
  has_test = has_test,
  p_overall = p_overall,
  p_nonlinear = p_nonlinear,
  note = note
)

jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")
