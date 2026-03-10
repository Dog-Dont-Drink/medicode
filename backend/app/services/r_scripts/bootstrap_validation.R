args <- commandArgs(trailingOnly = TRUE)
train_csv <- args[1]
output_json <- args[2]
plot_path <- args[3]
plot_pdf_path <- args[4]
dataset_name <- args[5]
model_type <- args[6]
outcome <- args[7]
time_var <- args[8]
event_var <- args[9]
predictors <- unlist(jsonlite::fromJSON(args[10]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[11]))
model_params <- jsonlite::fromJSON(args[12], simplifyVector = TRUE)
resamples_value <- as.integer(args[13])
seed_value <- as.integer(args[14])

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
ensure_package("ggplot2")
ensure_package("survival")
ensure_package("pROC")
library(jsonlite)
library(ggplot2)
library(survival)

set.seed(seed_value)
resamples_value <- if (is.na(resamples_value) || resamples_value < 20) 200L else resamples_value

fit_binary_model <- function(model_type, train_df, outcome, predictors, categorical_predictors, params) {
  if (model_type == "logistic") {
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(model_type = model_type, model = stats::glm(stats::as.formula(formula_text), data = train_df, family = stats::binomial()), train_df = train_df))
  }
  if (model_type == "random-forest") {
    ensure_package("randomForest")
    suppressPackageStartupMessages(library(randomForest))
    trees_value <- if (!is.null(params$trees)) as.integer(params$trees) else 500L
    mtry_value <- parse_mtry_arg(if (!is.null(params$mtry)) params$mtry else "sqrt(p)", length(predictors))
    rf_seed <- if (!is.null(params$seed)) as.integer(params$seed) else seed_value
    set.seed(rf_seed)
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(model_type = model_type, model = randomForest::randomForest(stats::as.formula(formula_text), data = train_df, ntree = trees_value, mtry = mtry_value), train_df = train_df))
  }
  if (model_type == "xgboost") {
    ensure_package("xgboost")
    eta_value <- if (!is.null(params$eta)) as.numeric(params$eta) else 0.05
    depth_value <- if (!is.null(params$depth)) as.integer(params$depth) else 4L
    rounds_value <- if (!is.null(params$rounds)) as.integer(params$rounds) else 300L
    xgb_seed <- if (!is.null(params$seed)) as.integer(params$seed) else seed_value
    set.seed(xgb_seed)
    design <- prepare_xgb_matrices(train_df, NULL, predictors, categorical_predictors)
    train_matrix <- xgboost::xgb.DMatrix(data = design$train_matrix, label = ifelse(train_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0))
    fit <- xgboost::xgb.train(
      params = list(objective = "binary:logistic", eval_metric = "auc", eta = eta_value, max_depth = depth_value, subsample = 0.8, colsample_bytree = 0.8, seed = xgb_seed),
      data = train_matrix,
      nrounds = rounds_value,
      verbose = 0
    )
    return(list(model_type = model_type, model = fit, train_df = train_df))
  }
  stop("Bootstrap 暂不支持当前二分类模型类型。", call. = FALSE)
}

predict_binary_model <- function(fit_bundle, new_df, outcome, predictors, categorical_predictors) {
  if (fit_bundle$model_type == "logistic") {
    return(as.numeric(stats::predict(fit_bundle$model, newdata = new_df, type = "response")))
  }
  if (fit_bundle$model_type == "random-forest") {
    aligned_df <- new_df
    for (predictor in predictors) {
      if (is.factor(fit_bundle$train_df[[predictor]])) {
        aligned_df[[predictor]] <- factor(aligned_df[[predictor]], levels = levels(fit_bundle$train_df[[predictor]]))
      }
    }
    return(as.numeric(stats::predict(fit_bundle$model, newdata = aligned_df, type = "prob")[, levels(fit_bundle$train_df[[outcome]])[2]]))
  }
  if (fit_bundle$model_type == "xgboost") {
    design <- prepare_xgb_matrices(fit_bundle$train_df, new_df, predictors, categorical_predictors)
    matrix <- xgboost::xgb.DMatrix(data = design$test_matrix)
    return(as.numeric(predict(fit_bundle$model, matrix)))
  }
  stop("Bootstrap 暂不支持当前二分类模型类型。", call. = FALSE)
}

binary_metric <- function(fit_bundle, df, outcome, predictors, categorical_predictors) {
  actual <- ifelse(df[[outcome]] == levels(fit_bundle$train_df[[outcome]])[2], 1, 0)
  probability <- predict_binary_model(fit_bundle, df, outcome, predictors, categorical_predictors)
  if (length(unique(actual)) < 2) {
    return(NA_real_)
  }
  as.numeric(pROC::auc(actual, probability, quiet = TRUE))
}

fit_survival_model <- function(train_df, time_var, event_var, predictors, categorical_predictors, model_type) {
  if (model_type != "cox") {
    stop("Bootstrap 暂不支持当前生存模型类型。", call. = FALSE)
  }
  formula_text <- paste0("survival::Surv(", backtick(time_var), ", event_status) ~ ", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
  fit <- survival::coxph(stats::as.formula(formula_text), data = train_df, x = TRUE, model = TRUE)
  list(model_type = model_type, model = fit, train_df = train_df)
}

survival_metric <- function(fit_bundle, df, time_var, event_var) {
  score <- as.numeric(stats::predict(fit_bundle$model, newdata = df, type = "lp"))
  compute_survival_concordance(df[[time_var]], df$event_status, score)
}

if (model_type == "cox") {
  raw_df <- read.csv(train_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  raw_df <- trim_dataframe_strings(raw_df)
  columns <- c(time_var, event_var, predictors)
  analysis_df <- raw_df[stats::complete.cases(raw_df[, columns, drop = FALSE]), columns, drop = FALSE]
  analysis_df[[time_var]] <- suppressWarnings(as.numeric(analysis_df[[time_var]]))
  analysis_df <- analysis_df[!is.na(analysis_df[[time_var]]) & analysis_df[[time_var]] > 0, , drop = FALSE]
  event_info <- prepare_survival_event(analysis_df, event_var)
  analysis_df <- event_info$data
  analysis_df$event_status <- event_info$event_numeric
  factor_info <- factorize_predictors(analysis_df, predictors, categorical_predictors)
  analysis_df <- factor_info$data
  valid_predictors <- factor_info$valid_predictors
  if (length(valid_predictors) == 0) {
    stop("Bootstrap 无可用 Cox 预测变量。", call. = FALSE)
  }

  apparent_fit <- fit_survival_model(analysis_df, time_var, event_var, valid_predictors, categorical_predictors, model_type)
  apparent_metric <- survival_metric(apparent_fit, analysis_df, time_var, event_var)
  optimism <- rep(NA_real_, resamples_value)
  for (i in seq_len(resamples_value)) {
    bootstrap_index <- sample(seq_len(nrow(analysis_df)), size = nrow(analysis_df), replace = TRUE)
    bootstrap_df <- analysis_df[bootstrap_index, , drop = FALSE]
    fit_i <- tryCatch(fit_survival_model(bootstrap_df, time_var, event_var, valid_predictors, categorical_predictors, model_type), error = function(e) NULL)
    if (is.null(fit_i)) {
      next
    }
    optimism[i] <- survival_metric(fit_i, bootstrap_df, time_var, event_var) - survival_metric(fit_i, analysis_df, time_var, event_var)
  }
  metric_label <- "C-index"
} else {
  raw_df <- read.csv(train_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  raw_df <- trim_dataframe_strings(raw_df)
  columns <- c(outcome, predictors)
  analysis_df <- raw_df[stats::complete.cases(raw_df[, columns, drop = FALSE]), columns, drop = FALSE]
  outcome_info <- prepare_binary_outcome(analysis_df, outcome)
  analysis_df <- outcome_info$data
  factor_info <- factorize_predictors(analysis_df, predictors, categorical_predictors)
  analysis_df <- factor_info$data
  valid_predictors <- factor_info$valid_predictors
  if (length(valid_predictors) == 0) {
    stop("Bootstrap 无可用二分类预测变量。", call. = FALSE)
  }

  apparent_fit <- fit_binary_model(model_type, analysis_df, outcome, valid_predictors, categorical_predictors, model_params)
  apparent_metric <- binary_metric(apparent_fit, analysis_df, outcome, valid_predictors, categorical_predictors)
  optimism <- rep(NA_real_, resamples_value)
  for (i in seq_len(resamples_value)) {
    bootstrap_index <- sample(seq_len(nrow(analysis_df)), size = nrow(analysis_df), replace = TRUE)
    bootstrap_df <- analysis_df[bootstrap_index, , drop = FALSE]
    fit_i <- tryCatch(fit_binary_model(model_type, bootstrap_df, outcome, valid_predictors, categorical_predictors, model_params), error = function(e) NULL)
    if (is.null(fit_i)) {
      next
    }
    optimism[i] <- binary_metric(fit_i, bootstrap_df, outcome, valid_predictors, categorical_predictors) - binary_metric(fit_i, analysis_df, outcome, valid_predictors, categorical_predictors)
  }
  metric_label <- "AUC"
}

optimism <- optimism[is.finite(optimism)]
mean_optimism <- if (length(optimism)) mean(optimism) else NA_real_
corrected_metric <- if (is.na(mean_optimism)) NA_real_ else apparent_metric - mean_optimism
summary_rows <- data.frame(
  metric = c("apparent", "mean_optimism", "optimism_corrected"),
  value = c(apparent_metric, mean_optimism, corrected_metric),
  stringsAsFactors = FALSE
)

optimism_df <- data.frame(optimism = optimism)
plot_obj <- ggplot(optimism_df, aes(x = optimism)) +
  geom_histogram(fill = "#0f766e", color = "#0f172a", bins = 30) +
  geom_vline(xintercept = mean_optimism, color = "#dc2626", linewidth = 0.9, linetype = "dashed") +
  labs(
    title = "Bootstrap Optimism Distribution",
    subtitle = paste0(metric_label, " optimism across ", length(optimism), " valid resamples"),
    x = "Optimism",
    y = "Count"
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    plot.title = element_text(face = "bold")
  )

png(filename = plot_path, width = 2200, height = 1600, res = 300)
tryCatch({
  print(plot_obj)
}, finally = {
  dev.off()
})
ggsave(plot_pdf_path, plot_obj, width = 7.2, height = 5.4, device = cairo_pdf)

result <- list(
  dataset_name = dataset_name,
  model_type = model_type,
  metric_label = metric_label,
  requested_resamples = resamples_value,
  completed_resamples = length(optimism),
  seed = seed_value,
  apparent_metric = apparent_metric,
  mean_optimism = mean_optimism,
  optimism_corrected_metric = corrected_metric,
  summary_rows = summary_rows,
  note = paste0("Bootstrap 内部验证已完成：", metric_label, " 校正后值为 ", formatC(corrected_metric, format = "f", digits = 3), "。")
)

jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")
