args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
dataset_name <- args[3]
outcome <- args[4]
predictors <- unlist(jsonlite::fromJSON(args[5]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[6]))
threshold_arg <- args[7]
selection_mode <- args[8]

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
library(jsonlite)

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
if (nrow(complete_df) < 10) {
  stop("有效样本量不足，单因素 Logistic 筛选至少需要 10 行完整观测。", call. = FALSE)
}

outcome_values <- unique(complete_df[[outcome]])
outcome_values <- outcome_values[!is.na(outcome_values)]
if (length(outcome_values) != 2) {
  stop("Logistic 回归因变量必须是二分类变量。", call. = FALSE)
}

if (is.numeric(complete_df[[outcome]])) {
  if (!all(sort(unique(complete_df[[outcome]])) %in% c(0, 1))) {
    stop("数值型 Logistic 因变量仅支持 0/1 编码。", call. = FALSE)
  }
  complete_df[[outcome]] <- factor(complete_df[[outcome]], levels = c(0, 1), labels = c("0", "1"))
} else {
  complete_df[[outcome]] <- factor(complete_df[[outcome]])
  if (nlevels(complete_df[[outcome]]) != 2) {
    stop("Logistic 回归因变量必须恰好有两个水平。", call. = FALSE)
  }
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
  stop("可用于单因素筛选的自变量不足，请检查是否存在单一取值或缺失。", call. = FALSE)
}

threshold_value <- suppressWarnings(as.numeric(threshold_arg))
if (selection_mode == "display_only" || is.na(threshold_value)) {
  threshold_value <- NA_real_
}

extract_logistic_rows <- function(formula_text, data) {
  fit <- stats::glm(stats::as.formula(formula_text), data = data, family = stats::binomial())
  fit_summary <- summary(fit)
  coef_matrix <- fit_summary$coefficients
  conf_low <- coef_matrix[, 1] - stats::qnorm(0.975) * coef_matrix[, 2]
  conf_high <- coef_matrix[, 1] + stats::qnorm(0.975) * coef_matrix[, 2]
  data.frame(
    term = rownames(coef_matrix),
    coefficient = unname(coef_matrix[, 1]),
    effect_value = unname(exp(coef_matrix[, 1])),
    std_error = unname(coef_matrix[, 2]),
    statistic = unname(coef_matrix[, 3]),
    p_value = unname(coef_matrix[, 4]),
    conf_low = unname(exp(conf_low)),
    conf_high = unname(exp(conf_high)),
    check.names = FALSE
  )
}

rows <- data.frame(
  predictor = character(0),
  term = character(0),
  coefficient = numeric(0),
  effect_value = numeric(0),
  std_error = numeric(0),
  statistic = numeric(0),
  p_value = numeric(0),
  conf_low = numeric(0),
  conf_high = numeric(0),
  selected = logical(0),
  check.names = FALSE
)

selected_predictors <- c()
for (predictor in valid_predictors) {
  predictor_formula <- paste(backtick(outcome), "~", backtick(predictor))
  predictor_rows <- tryCatch(
    extract_logistic_rows(predictor_formula, complete_df),
    error = function(e) NULL
  )
  if (is.null(predictor_rows) || nrow(predictor_rows) == 0) {
    next
  }
  predictor_rows <- subset(predictor_rows, term != "(Intercept)")
  if (nrow(predictor_rows) == 0) {
    next
  }
  is_selected <- rep(TRUE, nrow(predictor_rows))
  if (!is.na(threshold_value)) {
    is_selected <- !is.na(predictor_rows$p_value) & predictor_rows$p_value < threshold_value
  }
  predictor_rows$predictor <- predictor
  predictor_rows$selected <- is_selected
  rows <- rbind(rows, predictor_rows[, c("predictor", "term", "coefficient", "effect_value", "std_error", "statistic", "p_value", "conf_low", "conf_high", "selected")])
  if (selection_mode == "display_only") {
    selected_predictors <- c(selected_predictors, predictor)
  } else if (any(is_selected)) {
    selected_predictors <- c(selected_predictors, predictor)
  }
}

selected_predictors <- unique(selected_predictors)
if (length(selected_predictors) == 0 && selection_mode == "display_only") {
  selected_predictors <- valid_predictors
}

result <- list(
  dataset_name = dataset_name,
  outcome_variable = outcome,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  selection_mode = selection_mode,
  threshold = if (is.na(threshold_value)) NULL else threshold_value,
  selected_predictors = selected_predictors,
  coefficients = rows,
  note = if (selection_mode == "display_only") {
    "当前节点仅展示单因素 Logistic 结果，不执行筛除。"
  } else {
    paste0("按单因素 Logistic 回归 P < ", formatC(threshold_value, format = "f", digits = 2), " 进入后续分析。")
  }
)

write_json(result, output_json, auto_unbox = TRUE, pretty = TRUE, na = "null")
