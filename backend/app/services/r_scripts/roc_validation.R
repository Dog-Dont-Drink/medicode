args <- commandArgs(trailingOnly = TRUE)
train_csv <- args[1]
test_csv <- args[2]
output_json <- args[3]
plot_path <- args[4]
plot_pdf_path <- args[5]
dataset_name <- args[6]
model_type <- args[7]
outcome <- args[8]
predictors <- unlist(jsonlite::fromJSON(args[9]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[10]))
model_params <- jsonlite::fromJSON(args[11], simplifyVector = TRUE)
ci_mode <- args[12]
cutoff_rule <- args[13]

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
ensure_package("pROC")
library(jsonlite)
library(ggplot2)
suppressPackageStartupMessages(library(pROC))

fit_binary_model <- function(model_type, train_df, outcome, predictors, categorical_predictors, params) {
  if (model_type == "logistic") {
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(
      model_type = model_type,
      model = stats::glm(stats::as.formula(formula_text), data = train_df, family = stats::binomial()),
      train_df = train_df
    ))
  }

  if (model_type == "random-forest") {
    ensure_package("randomForest")
    suppressPackageStartupMessages(library(randomForest))
    trees_value <- if (!is.null(params$trees)) as.integer(params$trees) else 500L
    mtry_value <- parse_mtry_arg(if (!is.null(params$mtry)) params$mtry else "sqrt(p)", length(predictors))
    seed_value <- if (!is.null(params$seed)) as.integer(params$seed) else 2026L
    set.seed(seed_value)
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(
      model_type = model_type,
      model = randomForest::randomForest(
        formula = stats::as.formula(formula_text),
        data = train_df,
        ntree = trees_value,
        mtry = mtry_value,
        importance = TRUE
      ),
      train_df = train_df
    ))
  }

  if (model_type == "xgboost") {
    ensure_package("xgboost")
    eta_value <- if (!is.null(params$eta)) as.numeric(params$eta) else 0.05
    depth_value <- if (!is.null(params$depth)) as.integer(params$depth) else 4L
    rounds_value <- if (!is.null(params$rounds)) as.integer(params$rounds) else 300L
    seed_value <- if (!is.null(params$seed)) as.integer(params$seed) else 2026L
    set.seed(seed_value)
    design <- prepare_xgb_matrices(train_df, NULL, predictors, categorical_predictors)
    train_matrix <- xgboost::xgb.DMatrix(data = design$train_matrix, label = ifelse(train_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0))
    fit <- xgboost::xgb.train(
      params = list(
        objective = "binary:logistic",
        eval_metric = "auc",
        eta = eta_value,
        max_depth = depth_value,
        subsample = 0.8,
        colsample_bytree = 0.8,
        seed = seed_value
      ),
      data = train_matrix,
      nrounds = rounds_value,
      verbose = 0
    )
    return(list(
      model_type = model_type,
      model = fit,
      train_df = train_df
    ))
  }

  stop("ROC 验证暂不支持当前模型类型。", call. = FALSE)
}

predict_binary_model <- function(fit_bundle, new_df, outcome, predictors, categorical_predictors) {
  if (fit_bundle$model_type == "logistic") {
    aligned_df <- new_df
    for (predictor in predictors) {
      if (is.factor(fit_bundle$train_df[[predictor]])) {
        aligned_df[[predictor]] <- factor(aligned_df[[predictor]], levels = levels(fit_bundle$train_df[[predictor]]))
      }
    }
    return(as.numeric(stats::predict(fit_bundle$model, newdata = aligned_df, type = "response")))
  }
  if (fit_bundle$model_type == "random-forest") {
    train_df <- fit_bundle$train_df
    aligned_df <- new_df
    for (predictor in predictors) {
      if (is.factor(train_df[[predictor]])) {
        aligned_df[[predictor]] <- factor(aligned_df[[predictor]], levels = levels(train_df[[predictor]]))
      }
    }
    return(as.numeric(stats::predict(fit_bundle$model, newdata = aligned_df, type = "prob")[, levels(train_df[[outcome]])[2]]))
  }
  if (fit_bundle$model_type == "xgboost") {
    design <- prepare_xgb_matrices(fit_bundle$train_df, new_df, predictors, categorical_predictors)
    matrix <- xgboost::xgb.DMatrix(data = design$test_matrix)
    return(as.numeric(predict(fit_bundle$model, matrix)))
  }
  stop("ROC 验证暂不支持当前模型类型。", call. = FALSE)
}

train_df <- read.csv(train_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
train_df <- trim_dataframe_strings(train_df)
columns <- c(outcome, predictors)
train_df <- train_df[stats::complete.cases(train_df[, columns, drop = FALSE]), columns, drop = FALSE]
train_info <- prepare_binary_outcome(train_df, outcome)
train_df <- train_info$data
factor_info <- factorize_predictors(train_df, predictors, categorical_predictors)
train_df <- factor_info$data
valid_predictors <- factor_info$valid_predictors
if (length(valid_predictors) == 0) {
  stop("ROC 验证无可用预测变量。", call. = FALSE)
}

eval_df <- train_df
evaluation_dataset <- "训练集"
if (nzchar(test_csv) && test_csv != "NA" && file.exists(test_csv)) {
  raw_test <- read.csv(test_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  raw_test <- trim_dataframe_strings(raw_test)
  if (all(columns %in% names(raw_test))) {
    candidate_test <- raw_test[stats::complete.cases(raw_test[, columns, drop = FALSE]), columns, drop = FALSE]
    if (nrow(candidate_test) > 0) {
      eval_info <- prepare_binary_outcome(candidate_test, outcome)
      eval_df <- eval_info$data
      evaluation_dataset <- "测试集"
    }
  }
}

fit_bundle <- fit_binary_model(model_type, train_df, outcome, valid_predictors, categorical_predictors, model_params)

train_probability <- predict_binary_model(fit_bundle, train_df, outcome, valid_predictors, categorical_predictors)
train_actual <- ifelse(train_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0)
# NOTE:
# Tree models (e.g. randomForest) may output discrete probabilities with few unique values,
# which makes pROC's `smooth=TRUE` fail ("ROC curve not smoothable").
roc_train_raw <- pROC::roc(train_actual, train_probability, ci = TRUE, smooth = FALSE, quiet = TRUE)

test_probability <- predict_binary_model(fit_bundle, eval_df, outcome, valid_predictors, categorical_predictors)
test_actual <- ifelse(eval_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0)
roc_test_raw <- pROC::roc(test_actual, test_probability, ci = TRUE, smooth = FALSE, quiet = TRUE)

ci_method <- if (grepl("bootstrap", tolower(ci_mode), fixed = TRUE)) "bootstrap" else "delong"
train_auc_ci <- tryCatch(pROC::ci.auc(roc_train_raw, method = ci_method, boot.n = 200), error = function(e) c(NA_real_, NA_real_, NA_real_))
test_auc_ci <- tryCatch(pROC::ci.auc(roc_test_raw, method = ci_method, boot.n = 200), error = function(e) c(NA_real_, NA_real_, NA_real_))

train_coords <- pROC::coords(roc_train_raw, x = "best", best.method = "youden", ret = c("threshold", "sensitivity", "specificity"), transpose = FALSE)
train_youden <- as.numeric(train_coords$sensitivity) + as.numeric(train_coords$specificity) - 1
train_threshold <- as.numeric(train_coords$threshold)

test_coords <- pROC::coords(roc_test_raw, x = "best", best.method = "youden", ret = c("threshold", "sensitivity", "specificity"), transpose = FALSE)
test_youden <- as.numeric(test_coords$sensitivity) + as.numeric(test_coords$specificity) - 1
test_threshold <- as.numeric(test_coords$threshold)

threshold <- if (grepl("youden", tolower(cutoff_rule))) test_threshold else 0.5

train_metrics <- compute_binary_metrics(train_actual, train_probability, threshold = threshold)
test_metrics <- compute_binary_metrics(test_actual, test_probability, threshold = threshold)

to_roc_df <- function(roc_obj, label) {
  df <- data.frame(
    fpr = 1 - roc_obj$specificities,
    tpr = roc_obj$sensitivities,
    dataset = label,
    stringsAsFactors = FALSE
  )
  df <- df[stats::complete.cases(df[, c("fpr", "tpr")]), , drop = FALSE]
  df[order(df$fpr, df$tpr), , drop = FALSE]
}

roc_plot_df <- rbind(
  to_roc_df(roc_train_raw, "Train"),
  to_roc_df(roc_test_raw, "Test")
)

plot_obj <- ggplot(roc_plot_df, aes(x = fpr, y = tpr, color = dataset)) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "#94a3b8", linewidth = 0.8) +
  geom_line(linewidth = 1.1) +
  scale_color_manual(
    values = c("Train" = "#0f766e", "Test" = "#c2410c"),
    labels = c(
      Train = paste0("Train (AUC = ", formatC(as.numeric(pROC::auc(roc_train_raw)), format = "f", digits = 3), ")"),
      Test = paste0("Test (AUC = ", formatC(as.numeric(pROC::auc(roc_test_raw)), format = "f", digits = 3), ")")
    )
  ) +
  coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
  labs(
    title = "ROC Curve",
    x = "1 - Specificity",
    y = "Sensitivity",
    color = "Dataset"
  ) +
  theme_bw(base_size = 10) +
  theme(
    panel.grid.minor = element_blank(),
    plot.title = element_text(face = "bold", size = 11),
    legend.position = c(0.7, 0.2),
    legend.background = element_rect(fill = "white", color = "#e2e8f0"),
    legend.title = element_text(size = 9),
    legend.text = element_text(size = 8)
  )

png(filename = plot_path, width = 1800, height = 1400, res = 300)
tryCatch({
  print(plot_obj)
}, finally = {
  dev.off()
})
ggsave(plot_pdf_path, plot_obj, width = 6, height = 4.8, device = cairo_pdf)

result <- list(
  dataset_name = dataset_name,
  model_type = model_type,
  train_auc = as.numeric(pROC::auc(roc_train_raw)),
  train_auc_ci_low = as.numeric(train_auc_ci[1]),
  train_auc_ci_mid = as.numeric(train_auc_ci[2]),
  train_auc_ci_high = as.numeric(train_auc_ci[3]),
  train_youden_index = train_youden,
  train_optimal_threshold = train_threshold,
  train_sample_size = train_metrics$sample_size,
  train_event_count = train_metrics$event_count,
  train_accuracy = train_metrics$accuracy,
  train_sensitivity = train_metrics$sensitivity,
  train_specificity = train_metrics$specificity,
  train_precision = train_metrics$precision,
  train_npv = train_metrics$npv,
  train_f1 = train_metrics$f1,
  train_brier_score = train_metrics$brier_score,
  test_auc = as.numeric(pROC::auc(roc_test_raw)),
  test_auc_ci_low = as.numeric(test_auc_ci[1]),
  test_auc_ci_mid = as.numeric(test_auc_ci[2]),
  test_auc_ci_high = as.numeric(test_auc_ci[3]),
  test_youden_index = test_youden,
  test_optimal_threshold = test_threshold,
  test_sample_size = test_metrics$sample_size,
  test_event_count = test_metrics$event_count,
  test_accuracy = test_metrics$accuracy,
  test_sensitivity = test_metrics$sensitivity,
  test_specificity = test_metrics$specificity,
  test_precision = test_metrics$precision,
  test_npv = test_metrics$npv,
  test_f1 = test_metrics$f1,
  test_brier_score = test_metrics$brier_score,
  threshold = threshold,
  threshold_rule = cutoff_rule,
  accuracy = test_metrics$accuracy,
  sensitivity = test_metrics$sensitivity,
  specificity = test_metrics$specificity,
  precision = test_metrics$precision,
  npv = test_metrics$npv,
  f1 = test_metrics$f1,
  brier_score = test_metrics$brier_score,
  note = paste0(
    "训练集 AUC=", formatC(as.numeric(pROC::auc(roc_train_raw)), format = "f", digits = 3),
    " (95%CI: ", formatC(as.numeric(train_auc_ci[1]), format = "f", digits = 3), "-", formatC(as.numeric(train_auc_ci[3]), format = "f", digits = 3), "), ",
    "约登指数=", formatC(train_youden, format = "f", digits = 3), "；",
    "测试集 AUC=", formatC(as.numeric(pROC::auc(roc_test_raw)), format = "f", digits = 3),
    " (95%CI: ", formatC(as.numeric(test_auc_ci[1]), format = "f", digits = 3), "-", formatC(as.numeric(test_auc_ci[3]), format = "f", digits = 3), "), ",
    "约登指数=", formatC(test_youden, format = "f", digits = 3), "。"
  )
)

jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")
