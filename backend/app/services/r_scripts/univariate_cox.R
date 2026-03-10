args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
dataset_name <- args[3]
time_var <- args[4]
event_var <- args[5]
predictors <- unlist(jsonlite::fromJSON(args[6]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[7]))
threshold_arg <- args[8]
selection_mode <- args[9]

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
ensure_package("survival")
library(jsonlite)
library(survival)

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")

for (column_name in names(df)) {
  if (is.character(df[[column_name]])) {
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ""] <- NA
    df[[column_name]] <- trimmed
  }
}

complete_df <- df[stats::complete.cases(df[, c(time_var, event_var, predictors), drop = FALSE]), c(time_var, event_var, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < 10) {
  stop("有效样本量不足，单因素 Cox 筛选至少需要 10 行完整观测。", call. = FALSE)
}

complete_df[[time_var]] <- suppressWarnings(as.numeric(complete_df[[time_var]]))
if (any(is.na(complete_df[[time_var]]))) {
  stop("生存时间变量必须是数值型。", call. = FALSE)
}
if (any(complete_df[[time_var]] <= 0)) {
  stop("生存时间变量必须大于 0。", call. = FALSE)
}

event_values <- unique(complete_df[[event_var]])
event_values <- event_values[!is.na(event_values)]
if (length(event_values) != 2) {
  stop("事件变量必须是二分类变量。", call. = FALSE)
}

if (is.numeric(complete_df[[event_var]])) {
  numeric_values <- sort(unique(as.numeric(complete_df[[event_var]])))
  if (!all(numeric_values %in% c(0, 1))) {
    stop("数值型事件变量仅支持 0/1 编码。", call. = FALSE)
  }
  complete_df$event_status <- as.numeric(complete_df[[event_var]])
} else {
  complete_df[[event_var]] <- factor(complete_df[[event_var]])
  if (nlevels(complete_df[[event_var]]) != 2) {
    stop("事件变量必须恰好有两个水平。", call. = FALSE)
  }
  event_level <- levels(complete_df[[event_var]])[2]
  complete_df$event_status <- ifelse(complete_df[[event_var]] == event_level, 1, 0)
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

extract_cox_rows <- function(formula_text, data) {
  fit <- survival::coxph(stats::as.formula(formula_text), data = data, x = TRUE, model = TRUE)
  fit_summary <- summary(fit)
  coef_matrix <- fit_summary$coefficients
  conf_matrix <- fit_summary$conf.int
  data.frame(
    term = rownames(coef_matrix),
    coefficient = unname(coef_matrix[, "coef"]),
    effect_value = unname(conf_matrix[, "exp(coef)"]),
    std_error = unname(coef_matrix[, "se(coef)"]),
    statistic = unname(coef_matrix[, "z"]),
    p_value = unname(coef_matrix[, "Pr(>|z|)"]),
    conf_low = unname(conf_matrix[, "lower .95"]),
    conf_high = unname(conf_matrix[, "upper .95"]),
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
  predictor_formula <- paste0("survival::Surv(", backtick(time_var), ", event_status) ~ ", backtick(predictor))
  predictor_rows <- tryCatch(
    extract_cox_rows(predictor_formula, complete_df),
    error = function(e) NULL
  )
  if (is.null(predictor_rows) || nrow(predictor_rows) == 0) {
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
  time_variable = time_var,
  event_variable = event_var,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  selection_mode = selection_mode,
  threshold = if (is.na(threshold_value)) NULL else threshold_value,
  selected_predictors = selected_predictors,
  coefficients = rows,
  note = if (selection_mode == "display_only") {
    "当前节点仅展示单因素 Cox 结果，不执行筛除。"
  } else {
    paste0("按单因素 Cox 回归 P < ", formatC(threshold_value, format = "f", digits = 2), " 进入后续分析。")
  }
)

write_json(result, output_json, auto_unbox = TRUE, pretty = TRUE, na = "null")
