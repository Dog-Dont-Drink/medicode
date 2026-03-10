args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
plot_cv_path <- args[3]
plot_cv_pdf_path <- args[4]
plot_coef_path <- args[5]
plot_coef_pdf_path <- args[6]
dataset_name <- args[7]
outcome <- args[8]
predictors <- unlist(jsonlite::fromJSON(args[9]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[10]))
alpha_value <- as.numeric(args[11])
nfolds_value <- as.integer(args[12])

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
ensure_package("glmnet")
library(jsonlite)
library(glmnet)

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
if (nrow(complete_df) < max(10, nfolds_value)) {
  stop("有效样本量不足，LASSO 回归至少需要不低于折数的完整观测。", call. = FALSE)
}

family_name <- NA_character_
event_level <- NA_character_
reference_level <- NA_character_
if (is.numeric(complete_df[[outcome]])) {
  unique_values <- sort(unique(complete_df[[outcome]]))
  if (length(unique_values) == 2 && all(unique_values %in% c(0, 1))) {
    family_name <- "binomial"
    reference_level <- "0"
    event_level <- "1"
    y <- as.numeric(complete_df[[outcome]])
  } else {
    family_name <- "gaussian"
    y <- as.numeric(complete_df[[outcome]])
  }
} else {
  complete_df[[outcome]] <- factor(complete_df[[outcome]])
  if (nlevels(complete_df[[outcome]]) == 2) {
    family_name <- "binomial"
    reference_level <- levels(complete_df[[outcome]])[1]
    event_level <- levels(complete_df[[outcome]])[2]
    y <- ifelse(complete_df[[outcome]] == event_level, 1, 0)
  } else {
    stop("LASSO 当前仅支持连续因变量或二分类因变量。", call. = FALSE)
  }
}

for (predictor in predictors) {
  column <- complete_df[[predictor]]
  if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {
    complete_df[[predictor]] <- as.factor(column)
  }
}

x_formula <- paste("~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
x <- stats::model.matrix(stats::as.formula(x_formula), data = complete_df)[, -1, drop = FALSE]
if (ncol(x) == 0) {
  stop("LASSO 无法构造有效设计矩阵，请检查自变量取值。", call. = FALSE)
}

set.seed(123)
cv_fit <- glmnet::cv.glmnet(x, y, family = family_name, alpha = 1, nfolds = nfolds_value, standardize = TRUE)
full_fit <- glmnet::glmnet(x, y, family = family_name, alpha = 1, standardize = TRUE)

png(filename = plot_cv_path, width = 1600, height = 1200, res = 180)
plot(cv_fit)
#title("LASSO Cross-Validation Curve")
dev.off()

grDevices::pdf(file = plot_cv_pdf_path, width = 9, height = 7, useDingbats = FALSE)
plot(cv_fit)
#title("LASSO Cross-Validation Curve")
dev.off()

png(filename = plot_coef_path, width = 1600, height = 1200, res = 180)
plot(full_fit, xvar = "lambda", label = TRUE)
#title("LASSO Coefficient Path")
dev.off()

grDevices::pdf(file = plot_coef_pdf_path, width = 9, height = 7, useDingbats = FALSE)
plot(full_fit, xvar = "lambda", label = TRUE)
#title("LASSO Coefficient Path")
dev.off()

coef_min <- as.matrix(stats::coef(cv_fit, s = "lambda.min"))
coef_1se <- as.matrix(stats::coef(cv_fit, s = "lambda.1se"))
terms_all <- union(rownames(coef_min), rownames(coef_1se))
feature_df <- data.frame(
  term = terms_all,
  coefficient_lambda_min = as.numeric(coef_min[terms_all, 1]),
  coefficient_lambda_1se = as.numeric(coef_1se[terms_all, 1]),
  stringsAsFactors = FALSE,
  check.names = FALSE
)
feature_df$selected_at_lambda_min <- abs(feature_df$coefficient_lambda_min) > 0
feature_df$selected_at_lambda_1se <- abs(feature_df$coefficient_lambda_1se) > 0
feature_df <- feature_df[feature_df$term != "(Intercept)", , drop = FALSE]
feature_df <- feature_df[feature_df$selected_at_lambda_min | feature_df$selected_at_lambda_1se, , drop = FALSE]

result <- list(
  dataset_name = dataset_name,
  outcome_variable = outcome,
  predictor_variables = predictors,
  family = family_name,
  event_level = event_level,
  reference_level = reference_level,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  lambda_min = unname(cv_fit$lambda.min),
  lambda_1se = unname(cv_fit$lambda.1se),
  nonzero_count_lambda_min = sum(abs(as.matrix(coef(cv_fit, s = "lambda.min"))[-1, 1]) > 0),
  nonzero_count_lambda_1se = sum(abs(as.matrix(coef(cv_fit, s = "lambda.1se"))[-1, 1]) > 0),
  assumptions = list(
    "LASSO 通过 L1 惩罚进行变量筛选，适合高维或存在共线性的候选变量场景。",
    "lambda.min 通常给出预测误差最低的模型，lambda.1se 更保守、变量更少。",
    "图 1 为交叉验证曲线，图 2 为系数路径图，可辅助判断惩罚强度与变量进入顺序。",
    if (family_name == "binomial") "当前按二分类结局拟合 LASSO Logistic 回归。" else "当前按连续结局拟合 LASSO 线性回归。"
  ),
  selected_features = feature_df,
  note = paste0("设计矩阵共 ", ncol(x), " 列，建议结合 lambda.min 与 lambda.1se 两套结果综合判断变量筛选。")
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = "rows", null = "null", na = "null", pretty = TRUE), output_json)
