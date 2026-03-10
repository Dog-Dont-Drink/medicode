args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
residual_plot_png <- args[3]
residual_plot_pdf <- args[4]
fitted_plot_png <- args[5]
fitted_plot_pdf <- args[6]
dataset_name <- args[7]
outcome <- args[8]

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
backtick <- function(x) paste0("`", gsub("`", "", x, fixed = TRUE), "`")

ensure_package("jsonlite")
ensure_package("ggplot2")
ensure_package("lmtest")

library(jsonlite)
library(ggplot2)
library(lmtest)

predictors <- unlist(jsonlite::fromJSON(args[9]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[10]))
alpha_value <- as.numeric(args[11])

theme_set(
  theme_classic(base_size = 12) +
    theme(
      plot.title = element_text(face = "bold", size = 14, colour = "#14532d", hjust = 0),
      plot.subtitle = element_text(size = 10, colour = "#4b5563", hjust = 0),
      axis.title = element_text(face = "bold", colour = "#1f2937", size = 12),
      axis.text = element_text(colour = "#475569", size = 10),
      axis.line = element_line(colour = "#374151", linewidth = 0.75),
      axis.ticks = element_line(colour = "#374151", linewidth = 0.65),
      axis.ticks.length = unit(2.2, "mm"),
      panel.border = element_rect(colour = "#374151", fill = NA, linewidth = 0.75),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")

for (column_name in names(df)) {
  if (is.character(df[[column_name]])) {
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ""] <- NA
    df[[column_name]] <- trimmed
  }
}

complete_df <- df[stats::complete.cases(df[, c(outcome, predictors), drop = FALSE]), c(outcome, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < 5) {
  stop("有效样本量不足，线性回归至少需要 5 行完整观测。", call. = FALSE)
}

if (!is.numeric(complete_df[[outcome]])) {
  stop("线性回归的因变量必须是数值型。", call. = FALSE)
}

valid_predictors <- c()
for (predictor in predictors) {
  column <- complete_df[[predictor]]
  unique_values <- unique(column[!is.na(column)])
  if (length(unique_values) >= 2) {
    if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {
      complete_df[[predictor]] <- as.factor(column)
    }
    valid_predictors <- c(valid_predictors, predictor)
  }
}

if (length(valid_predictors) == 0) {
  stop("可用于建模的自变量不足，请检查是否存在单一取值或缺失。", call. = FALSE)
}

formula_text <- paste(backtick(outcome), "~", paste(vapply(valid_predictors, backtick, character(1)), collapse = " + "))
fit <- stats::lm(stats::as.formula(formula_text), data = complete_df)
fit_summary <- summary(fit)
coef_matrix <- fit_summary$coefficients
conf_matrix <- suppressMessages(stats::confint(fit, level = 1 - alpha_value))
residual_values <- residuals(fit)
fitted_values <- fitted(fit)
observed_values <- complete_df[[outcome]]

residual_method <- "Shapiro-Wilk"
residual_p <- NA_real_
residual_note <- "残差正态性未检查"
if (length(residual_values) >= 3 && length(unique(residual_values)) > 1) {
  if (length(residual_values) <= 5000) {
    residual_test <- stats::shapiro.test(residual_values)
    residual_p <- residual_test$p.value
    residual_note <- paste0("残差正态性 Shapiro-Wilk P=", formatC(residual_p, format = "f", digits = 3))
  } else {
    residual_method <- "样本量>5000，未执行 Shapiro-Wilk"
    residual_note <- residual_method
  }
} else if (length(unique(residual_values)) <= 1) {
  residual_method <- "残差取值完全相同"
  residual_note <- "残差无离散度，无法执行正态性检验"
}
residual_passed <- !is.na(residual_p) && residual_p >= alpha_value

bp_method <- "Breusch-Pagan"
bp_p <- NA_real_
bp_note <- "异方差未检查"
bp_passed <- FALSE
bp_result <- tryCatch(
  lmtest::bptest(fit),
  error = function(e) NULL
)
if (!is.null(bp_result)) {
  bp_p <- bp_result$p.value
  bp_note <- paste0("Breusch-Pagan P=", formatC(bp_p, format = "f", digits = 3))
  bp_passed <- !is.na(bp_p) && bp_p >= alpha_value
} else {
  bp_method <- "Breusch-Pagan 不可用"
  bp_note <- "未能完成异方差检验"
}

coef_df <- data.frame(
  term = rownames(coef_matrix),
  estimate = unname(coef_matrix[, 1]),
  std_error = unname(coef_matrix[, 2]),
  statistic = unname(coef_matrix[, 3]),
  p_value = unname(coef_matrix[, 4]),
  conf_low = unname(conf_matrix[, 1]),
  conf_high = unname(conf_matrix[, 2]),
  check.names = FALSE
)

diagnostic_df <- data.frame(
  fitted = unname(fitted_values),
  residual = unname(residual_values),
  observed = unname(observed_values)
)

green_dark <- "#047857"
green_mid <- "#10b981"
green_light <- "#a7f3d0"
line_gray <- "#94a3b8"

residual_plot <- ggplot(diagnostic_df, aes(x = fitted, y = residual)) +
  geom_hline(yintercept = 0, colour = line_gray, linewidth = 0.7, linetype = "dashed") +
  geom_point(shape = 21, size = 2.8, stroke = 0.35, colour = green_dark, fill = green_light, alpha = 0.9) +
  geom_smooth(method = "loess", se = FALSE, colour = green_mid, linewidth = 0.9, span = 0.9) +
  scale_x_continuous(expand = expansion(mult = c(0.03, 0.03))) +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.05))) +
  labs(
    title = "Residuals vs Fitted",
    subtitle = paste0("Shapiro-Wilk P=", ifelse(is.na(residual_p), "NA", formatC(residual_p, format = "f", digits = 3))),
    x = "Fitted value",
    y = "Residual"
  )

fitted_plot <- ggplot(diagnostic_df, aes(x = fitted, y = observed)) +
  geom_abline(intercept = 0, slope = 1, colour = line_gray, linewidth = 0.7, linetype = "dashed") +
  geom_point(shape = 21, size = 2.8, stroke = 0.35, colour = green_dark, fill = green_light, alpha = 0.9) +
  geom_smooth(method = "lm", se = FALSE, colour = green_mid, linewidth = 0.9) +
  scale_x_continuous(expand = expansion(mult = c(0.03, 0.03))) +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.05))) +
  labs(
    title = "Observed vs Fitted",
    subtitle = paste0("R²=", formatC(unname(fit_summary$r.squared), format = "f", digits = 3)),
    x = "Fitted value",
    y = "Observed value"
  )

ggsave(filename = residual_plot_png, plot = residual_plot, width = 7.2, height = 5.2, dpi = 300, bg = "white")
ggsave(filename = residual_plot_pdf, plot = residual_plot, width = 7.2, height = 5.2, device = "pdf", bg = "white")
ggsave(filename = fitted_plot_png, plot = fitted_plot, width = 7.2, height = 5.2, dpi = 300, bg = "white")
ggsave(filename = fitted_plot_pdf, plot = fitted_plot, width = 7.2, height = 5.2, device = "pdf", bg = "white")

fstat <- fit_summary$fstatistic
model_p <- if (is.null(fstat)) NA_real_ else stats::pf(fstat[1], fstat[2], fstat[3], lower.tail = FALSE)

result <- list(
  dataset_name = dataset_name,
  outcome_variable = outcome,
  predictor_variables = valid_predictors,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  r_squared = unname(fit_summary$r.squared),
  adjusted_r_squared = unname(fit_summary$adj.r.squared),
  residual_standard_error = unname(fit_summary$sigma),
  f_statistic = if (is.null(fstat)) NA_real_ else unname(fstat[1]),
  df_model = if (is.null(fstat)) NA_real_ else unname(fstat[2]),
  df_residual = if (is.null(fstat)) NA_real_ else unname(fstat[3]),
  model_p_value = model_p,
  formula = formula_text,
  assumptions = list(
    "因变量应为连续数值型，自变量可为数值型或分类变量。",
    "模型默认使用完整案例进行拟合，含缺失值的记录已剔除。",
    residual_note,
    bp_note,
    "请结合残差图、拟合图、异常值和共线性进一步判断模型稳健性。"
  ),
  residual_normality_method = residual_method,
  residual_normality_p_value = residual_p,
  residual_normality_passed = residual_passed,
  homoscedasticity_test_method = bp_method,
  homoscedasticity_p_value = bp_p,
  homoscedasticity_passed = bp_passed,
  coefficients = coef_df,
  note = paste0("模型共纳入 ", nrow(complete_df), " 条完整记录；若分类变量存在多个水平，系数以参考水平为基线解释。")
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = "rows", null = "null", na = "null", pretty = TRUE), output_json)
