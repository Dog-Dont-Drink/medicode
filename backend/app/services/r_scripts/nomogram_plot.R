args <- commandArgs(trailingOnly = TRUE)
train_csv <- args[1]
test_csv <- args[2]
output_json <- args[3]
plot_png_path <- args[4]
plot_pdf_path <- args[5]
dataset_name <- args[6]
model_type <- args[7]
outcome <- args[8]
time_var <- args[9]
event_var <- args[10]
predictors_json <- args[11]
categorical_predictors_json <- args[12]
model_params_json <- args[13]
scale_points <- suppressWarnings(as.integer(args[14]))
timepoint_text <- args[15]

options(repos = c(CRAN = Sys.getenv("MEDICODE_R_PACKAGE_REPO", unset = "https://cloud.r-project.org")))
auto_install_enabled <- tolower(Sys.getenv("MEDICODE_R_AUTO_INSTALL_ENABLED", unset = "true")) %in% c("1", "true", "yes")
ensure_package <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (!isTRUE(auto_install_enabled)) {
      stop(paste0("缺少 R 包: ", pkg), call. = FALSE)
    }
    install.packages(pkg, repos = getOption("repos")[["CRAN"]])
  }
}
script_dir <- dirname(normalizePath(sub("^--file=", "", commandArgs(FALSE)[grep("^--file=", commandArgs(FALSE))][1])))
source(file.path(script_dir, "ml_model_common.R"))

ensure_package("jsonlite")
ensure_package("survival")
ensure_package("rms")
ensure_package("pROC")
library(jsonlite)
library(survival)
library(rms)

predictors <- unlist(jsonlite::fromJSON(predictors_json))
categorical_predictors <- unlist(jsonlite::fromJSON(categorical_predictors_json))
model_params <- jsonlite::fromJSON(model_params_json, simplifyVector = TRUE)

open_png_device <- function(path, width, height, res) {
  tryCatch(
    grDevices::png(filename = path, width = width, height = height, res = res, type = "cairo"),
    error = function(e) grDevices::png(filename = path, width = width, height = height, res = res)
  )
}

extract_first_number <- function(text) {
  if (is.null(text) || !nzchar(trimws(text))) return(NA_real_)
  match <- regmatches(text, regexpr("[0-9]+\\.?[0-9]*", text))
  if (!length(match) || !nzchar(match)) return(NA_real_)
  suppressWarnings(as.numeric(match))
}

normalize_scale_points <- function(value) {
  if (!is.na(value) && value >= 50) return(as.integer(value))
  parsed <- extract_first_number(as.character(value))
  if (!is.na(parsed) && parsed >= 50) return(as.integer(parsed))
  100L
}

scale_points <- normalize_scale_points(scale_points)

parse_timepoint <- function(text, fallback) {
  num <- extract_first_number(as.character(text))
  if (is.na(num) || num <= 0) {
    return(fallback)
  }
  num
}

read_and_prepare <- function(path, required_columns) {
  df <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  df <- trim_dataframe_strings(df)
  df <- df[stats::complete.cases(df[, required_columns, drop = FALSE]), required_columns, drop = FALSE]
  df
}

coerce_binary_numeric <- function(series, event_level) {
  if (is.numeric(series)) {
    return(ifelse(as.numeric(series) == 1, 1, 0))
  }
  as.numeric(ifelse(as.character(series) == event_level, 1, 0))
}

align_factor_levels <- function(train_df, test_df, predictors) {
  aligned <- test_df
  for (predictor in predictors) {
    if (predictor %in% names(train_df) && is.factor(train_df[[predictor]])) {
      aligned[[predictor]] <- factor(aligned[[predictor]], levels = levels(train_df[[predictor]]))
    }
  }
  aligned
}

has_test <- FALSE
train_metrics <- list()
test_metrics <- NULL
note_lines <- c()
timepoint_value_used <- NA_real_

if (model_type == "logistic") {
  required_columns <- c(outcome, predictors)
  train_df <- read_and_prepare(train_csv, required_columns)
  if (nrow(train_df) < 10) {
    stop("有效样本量不足，列线图至少需要 10 行完整观测。", call. = FALSE)
  }

  train_info <- prepare_binary_outcome(train_df, outcome)
  train_df <- train_info$data
  factor_info <- factorize_predictors(train_df, predictors, categorical_predictors)
  train_df <- factor_info$data
  valid_predictors <- factor_info$valid_predictors
  if (length(valid_predictors) == 0) {
    stop("列线图无可用预测变量。", call. = FALSE)
  }

  dd <- rms::datadist(train_df)
  options(datadist = "dd")
  formula_text <- paste(backtick(outcome), "~", paste(vapply(valid_predictors, backtick, character(1)), collapse = " + "))
  fit <- rms::lrm(stats::as.formula(formula_text), data = train_df, x = TRUE, y = TRUE)

  train_prob <- as.numeric(stats::predict(fit, type = "fitted"))
  train_metrics <- compute_binary_metrics(train_info$outcome_numeric, train_prob, threshold = 0.5)

  if (nzchar(test_csv) && test_csv != "NA" && file.exists(test_csv)) {
    raw_test <- read_and_prepare(test_csv, required_columns)
    if (nrow(raw_test) > 0) {
      aligned_test <- align_factor_levels(train_df, raw_test, valid_predictors)
      test_prob <- as.numeric(stats::predict(fit, newdata = aligned_test, type = "fitted"))
      test_actual <- coerce_binary_numeric(aligned_test[[outcome]], train_info$event_level)
      test_metrics <- compute_binary_metrics(test_actual, test_prob, threshold = 0.5)
      has_test <- TRUE
    }
  }

  risk_fun <- function(x) 1 / (1 + exp(-x))
  nom <- rms::nomogram(
    fit,
    fun = risk_fun,
    funlabel = "Predicted risk",
    fun.at = c(0.01, 0.05, seq(0.1, 0.9, 0.1), 0.95, 0.99),
    maxscale = scale_points,
    lp = FALSE
  )

  open_png_device(plot_png_path, width = 2600, height = 1800, res = 300)
  tryCatch(
    {
      par(mar = c(4.2, 3.8, 3.2, 1.6), mgp = c(2.2, 0.7, 0))
      plot(nom, xfrac = 0.42, lmgp = 0.24, cex.axis = 0.84, cex.var = 0.92, col.grid = "#CBD5E1")
      title(main = "Nomogram (Logistic regression)", cex.main = 1.15, font.main = 2)
    },
    finally = {
      grDevices::dev.off()
    }
  )
  grDevices::cairo_pdf(plot_pdf_path, width = 9.2, height = 6.2)
  tryCatch(
    {
      par(mar = c(4.2, 3.8, 3.2, 1.6), mgp = c(2.2, 0.7, 0))
      plot(nom, xfrac = 0.42, lmgp = 0.24, cex.axis = 0.84, cex.var = 0.92, col.grid = "#CBD5E1")
      title(main = "Nomogram (Logistic regression)", cex.main = 1.15, font.main = 2)
    },
    finally = {
      grDevices::dev.off()
    }
  )

  note_lines <- c(
    paste0("Nomogram based on logistic regression. scale_points=", scale_points, "."),
    paste0("Predictors: ", paste(valid_predictors, collapse = ", "), ".")
  )
} else if (model_type == "cox") {
  required_columns <- c(time_var, event_var, predictors)
  train_df <- read_and_prepare(train_csv, required_columns)
  if (nrow(train_df) < 10) {
    stop("有效样本量不足，列线图至少需要 10 行完整观测。", call. = FALSE)
  }

  train_df[[time_var]] <- suppressWarnings(as.numeric(train_df[[time_var]]))
  if (any(is.na(train_df[[time_var]]))) {
    stop("生存时间变量必须是数值型。", call. = FALSE)
  }
  if (any(train_df[[time_var]] <= 0)) {
    stop("生存时间变量必须大于 0。", call. = FALSE)
  }

  event_info <- prepare_survival_event(train_df, event_var)
  train_df <- event_info$data
  train_df$event_status <- event_info$event_numeric

  factor_info <- factorize_predictors(train_df, predictors, categorical_predictors)
  train_df <- factor_info$data
  valid_predictors <- factor_info$valid_predictors
  if (length(valid_predictors) == 0) {
    stop("列线图无可用预测变量。", call. = FALSE)
  }

  fallback_timepoint <- stats::median(train_df[[time_var]], na.rm = TRUE)
  timepoint_value <- parse_timepoint(timepoint_text, fallback_timepoint)
  if (!is.finite(timepoint_value) || timepoint_value <= 0) {
    timepoint_value <- fallback_timepoint
  }
  timepoint_value_used <- timepoint_value

  dd <- rms::datadist(train_df)
  options(datadist = "dd")
  formula_text <- paste0("survival::Surv(", backtick(time_var), ", event_status) ~ ", paste(vapply(valid_predictors, backtick, character(1)), collapse = " + "))
  fit <- rms::cph(stats::as.formula(formula_text), data = train_df, x = TRUE, y = TRUE, surv = TRUE, time.inc = timepoint_value)

  train_lp <- as.numeric(stats::predict(fit, type = "lp"))
  train_c <- compute_survival_concordance(train_df[[time_var]], train_df$event_status, train_lp)
  train_metrics <- list(sample_size = as.integer(nrow(train_df)), event_count = as.integer(sum(train_df$event_status == 1)), concordance = train_c)

  if (nzchar(test_csv) && test_csv != "NA" && file.exists(test_csv)) {
    raw_test <- read_and_prepare(test_csv, required_columns)
    if (nrow(raw_test) > 0) {
      raw_test[[time_var]] <- suppressWarnings(as.numeric(raw_test[[time_var]]))
      if (!any(is.na(raw_test[[time_var]])) && !any(raw_test[[time_var]] <= 0)) {
        aligned_test <- align_factor_levels(train_df, raw_test, valid_predictors)
        event_numeric <- if (is.numeric(aligned_test[[event_var]])) {
          ifelse(as.numeric(aligned_test[[event_var]]) == 1, 1, 0)
        } else {
          ifelse(as.character(aligned_test[[event_var]]) == event_info$event_level, 1, 0)
        }
        aligned_test$event_status <- as.numeric(event_numeric)
        test_lp <- as.numeric(stats::predict(fit, newdata = aligned_test, type = "lp"))
        test_c <- compute_survival_concordance(aligned_test[[time_var]], aligned_test$event_status, test_lp)
        test_metrics <- list(sample_size = as.integer(nrow(aligned_test)), event_count = as.integer(sum(aligned_test$event_status == 1)), concordance = test_c)
        has_test <- TRUE
      }
    }
  }

  surv_fun <- rms::Survival(fit)
  fun_surv <- function(lp) surv_fun(timepoint_value, lp)
  fun_label <- paste0("Survival probability at t=", formatC(timepoint_value, format = "f", digits = 2))
  nom <- rms::nomogram(
    fit,
    fun = list(fun_surv),
    funlabel = fun_label,
    maxscale = scale_points,
    lp = TRUE
  )

  open_png_device(plot_png_path, width = 2700, height = 1800, res = 300)
  tryCatch(
    {
      par(mar = c(4.2, 3.8, 3.2, 1.6), mgp = c(2.2, 0.7, 0))
      plot(nom, xfrac = 0.42, lmgp = 0.24, cex.axis = 0.84, cex.var = 0.92, col.grid = "#CBD5E1")
      title(main = "Nomogram (Cox regression)", cex.main = 1.15, font.main = 2)
    },
    finally = {
      grDevices::dev.off()
    }
  )
  grDevices::cairo_pdf(plot_pdf_path, width = 9.4, height = 6.2)
  tryCatch(
    {
      par(mar = c(4.2, 3.8, 3.2, 1.6), mgp = c(2.2, 0.7, 0))
      plot(nom, xfrac = 0.42, lmgp = 0.24, cex.axis = 0.84, cex.var = 0.92, col.grid = "#CBD5E1")
      title(main = "Nomogram (Cox regression)", cex.main = 1.15, font.main = 2)
    },
    finally = {
      grDevices::dev.off()
    }
  )

  note_lines <- c(
    paste0("Nomogram based on Cox regression. scale_points=", scale_points, "."),
    paste0("timepoint=", formatC(timepoint_value, format = "f", digits = 2), " (same unit as survival time variable)."),
    paste0("Predictors: ", paste(valid_predictors, collapse = ", "), ".")
  )
} else {
  stop("列线图仅支持 logistic 或 cox 模型。", call. = FALSE)
}

result <- list(
  dataset_name = dataset_name,
  model_type = model_type,
  has_test = has_test,
  scale_points = scale_points,
  timepoint = timepoint_value_used,
  train_metrics = train_metrics,
  test_metrics = test_metrics,
  note = paste(note_lines, collapse = " ")
)

jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")
