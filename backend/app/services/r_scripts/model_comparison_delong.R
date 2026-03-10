args <- commandArgs(trailingOnly = TRUE)
train_csv <- args[1]
test_csv <- args[2]
output_json <- args[3]
train_plot_path <- args[4]
train_plot_pdf_path <- args[5]
test_plot_path <- args[6]
test_plot_pdf_path <- args[7]
dataset_name <- args[8]
outcome <- args[9]
model_specs <- jsonlite::fromJSON(args[10], simplifyVector = FALSE)
categorical_predictors <- unlist(jsonlite::fromJSON(args[11]))

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

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

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

spec_names <- vapply(model_specs, function(x) as.character(x$name %||% ""), character(1))
if (length(unique(spec_names)) != length(spec_names)) {
  # Make names unique.
  spec_names <- make.unique(spec_names, sep = " #")
  for (i in seq_along(model_specs)) model_specs[[i]]$name <- spec_names[i]
}

is_non_ascii <- function(text) grepl("[^ -~]", text)
normalize_model_type_label <- function(model_type) {
  if (model_type %in% c("logistic")) return("Logistic")
  if (model_type %in% c("random-forest", "random_forest", "randomForest")) return("RandomForest")
  if (model_type %in% c("xgboost")) return("XGBoost")
  "Model"
}

model_display_map <- list()
type_counts <- list()
for (spec in model_specs) {
  model_name <- as.character(spec$name)
  model_type <- as.character(spec$model_type)
  type_label <- normalize_model_type_label(model_type)
  if (is.null(type_counts[[type_label]])) type_counts[[type_label]] <- 0L
  type_counts[[type_label]] <- type_counts[[type_label]] + 1L
  suffix <- if (type_counts[[type_label]] > 1) paste0(" #", type_counts[[type_label]]) else ""
  display <- if (is_non_ascii(model_name)) paste0(type_label, suffix) else model_name
  model_display_map[[model_name]] <- display
}

union_predictors <- unique(unlist(lapply(model_specs, function(spec) unlist(spec$predictors))))
required_columns <- unique(c(outcome, union_predictors))
missing_cols <- setdiff(required_columns, names(train_df))
if (length(missing_cols) > 0) {
  stop(paste0("训练集缺少字段: ", paste(missing_cols, collapse = ", ")), call. = FALSE)
}
train_df <- train_df[stats::complete.cases(train_df[, required_columns, drop = FALSE]), required_columns, drop = FALSE]
if (nrow(train_df) < 20) {
  stop("模型比较至少需要 20 行完整观测。", call. = FALSE)
}

if (has_test) {
  missing_test <- setdiff(required_columns, names(test_df))
  if (length(missing_test) > 0) {
    # allow no test if incomplete
    has_test <- FALSE
    test_df <- NULL
  } else {
    test_df <- test_df[stats::complete.cases(test_df[, required_columns, drop = FALSE]), required_columns, drop = FALSE]
    if (nrow(test_df) < 5) {
      has_test <- FALSE
      test_df <- NULL
    }
  }
}

outcome_info <- prepare_binary_outcome(train_df, outcome)
train_df <- outcome_info$data
train_actual <- outcome_info$outcome_numeric
event_level <- outcome_info$event_level
reference_level <- outcome_info$reference_level

if (has_test) {
  # Align test outcome levels to training (avoid positive-class mismatch).
  if (is.numeric(test_df[[outcome]])) {
    numeric_values <- sort(unique(as.numeric(test_df[[outcome]])))
    numeric_values <- numeric_values[!is.na(numeric_values)]
    if (length(numeric_values) != 2) {
      has_test <- FALSE
      test_df <- NULL
      test_actual <- numeric(0)
    } else {
      train_levels <- suppressWarnings(as.numeric(c(reference_level, event_level)))
      if (any(is.na(train_levels)) || !all(train_levels %in% numeric_values)) {
        # fallback: still map by sorted numeric order
        ref_num <- numeric_values[1]
        evt_num <- numeric_values[2]
        reference_level <- as.character(ref_num)
        event_level <- as.character(evt_num)
      }
      test_df[[outcome]] <- factor(as.numeric(test_df[[outcome]]), levels = suppressWarnings(as.numeric(c(reference_level, event_level))), labels = c(reference_level, event_level))
      test_actual <- ifelse(test_df[[outcome]] == event_level, 1, 0)
      test_actual <- as.numeric(test_actual)
    }
  } else {
    test_df[[outcome]] <- factor(test_df[[outcome]])
    if (!all(c(reference_level, event_level) %in% levels(test_df[[outcome]]))) {
      has_test <- FALSE
      test_df <- NULL
      test_actual <- numeric(0)
    } else {
      test_df[[outcome]] <- factor(test_df[[outcome]], levels = c(reference_level, event_level))
      test_actual <- ifelse(test_df[[outcome]] == event_level, 1, 0)
      test_actual <- as.numeric(test_actual)
    }
  }
} else {
  test_actual <- numeric(0)
}

factorize_for_predictors <- function(df, predictors, categorical_predictors) {
  for (predictor in predictors) {
    if (!predictor %in% names(df)) next
    if (predictor %in% categorical_predictors || is.character(df[[predictor]]) || is.logical(df[[predictor]])) {
      df[[predictor]] <- as.factor(df[[predictor]])
    }
  }
  df
}

fit_and_predict <- function(spec, train_df, test_df, outcome, actual_event_level, categorical_predictors) {
  model_type <- as.character(spec$model_type)
  predictors <- unlist(spec$predictors)
  params <- spec$params

  train_local <- factorize_for_predictors(train_df, predictors, categorical_predictors)
  test_local <- if (!is.null(test_df)) factorize_for_predictors(test_df, predictors, categorical_predictors) else NULL

  if (model_type == "logistic") {
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    fit <- stats::glm(stats::as.formula(formula_text), data = train_local, family = stats::binomial())
    prob_train <- as.numeric(stats::predict(fit, newdata = train_local, type = "response"))
    prob_test <- NULL
    if (!is.null(test_local)) {
      for (predictor in predictors) {
        if (is.factor(train_local[[predictor]])) {
          test_local[[predictor]] <- factor(test_local[[predictor]], levels = levels(train_local[[predictor]]))
        }
      }
      prob_test <- as.numeric(stats::predict(fit, newdata = test_local, type = "response"))
    }
    return(list(prob_train = prob_train, prob_test = prob_test))
  }

  if (model_type %in% c("random-forest", "random_forest", "randomForest")) {
    ensure_package("randomForest")
    suppressPackageStartupMessages(library(randomForest))
    trees_value <- if (!is.null(params$trees)) as.integer(params$trees) else 500L
    mtry_raw <- if (!is.null(params$mtry)) as.character(params$mtry) else "sqrt(p)"
    seed_value <- if (!is.null(params$seed)) as.integer(params$seed) else 2026L
    set.seed(seed_value)
    mtry_value <- parse_mtry_arg(mtry_raw, length(predictors))
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    fit <- randomForest::randomForest(
      formula = stats::as.formula(formula_text),
      data = train_local,
      ntree = trees_value,
      mtry = mtry_value
    )
    prob_train <- as.numeric(stats::predict(fit, newdata = train_local, type = "prob")[, event_level])
    prob_test <- NULL
    if (!is.null(test_local)) {
      for (predictor in predictors) {
        if (is.factor(train_local[[predictor]])) {
          test_local[[predictor]] <- factor(test_local[[predictor]], levels = levels(train_local[[predictor]]))
        }
      }
      prob_test <- as.numeric(stats::predict(fit, newdata = test_local, type = "prob")[, event_level])
    }
    return(list(prob_train = prob_train, prob_test = prob_test))
  }

  if (model_type == "xgboost") {
    ensure_package("xgboost")
    suppressPackageStartupMessages(library(xgboost))
    eta_value <- if (!is.null(params$eta)) as.numeric(params$eta) else 0.05
    depth_value <- if (!is.null(params$depth)) as.integer(params$depth) else 4L
    rounds_value <- if (!is.null(params$rounds)) as.integer(params$rounds) else 300L
    seed_value <- if (!is.null(params$seed)) as.integer(params$seed) else 2026L
    set.seed(seed_value)
    design <- prepare_xgb_matrices(train_local, test_local, predictors, categorical_predictors)
    train_matrix <- xgboost::xgb.DMatrix(data = design$train_matrix, label = ifelse(train_local[[outcome]] == actual_event_level, 1, 0))
    test_matrix <- if (!is.null(design$test_matrix)) xgboost::xgb.DMatrix(data = design$test_matrix) else NULL
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
    prob_train <- as.numeric(predict(fit, train_matrix))
    prob_test <- if (!is.null(test_matrix)) as.numeric(predict(fit, test_matrix)) else NULL
    return(list(prob_train = prob_train, prob_test = prob_test))
  }

  stop(paste0("不支持的模型类型: ", model_type), call. = FALSE)
}

roc_objects_train <- list()
roc_objects_test <- list()
auc_rows <- list()

train_event_count <- as.integer(sum(train_actual == 1))
test_event_count <- if (has_test) as.integer(sum(test_actual == 1)) else 0L

for (spec in model_specs) {
  model_name <- as.character(spec$name)
  model_type <- as.character(spec$model_type)
  preds <- fit_and_predict(spec, train_df, test_df, outcome, event_level, categorical_predictors)
  roc_train <- pROC::roc(train_actual, preds$prob_train, quiet = TRUE, ci = FALSE, smooth = FALSE)
  roc_objects_train[[model_name]] <- roc_train
  auc_train <- as.numeric(pROC::auc(roc_train))
  auc_rows[[length(auc_rows) + 1]] <- c("训练集", model_name, model_type, length(train_actual), train_event_count, auc_train)

  if (has_test && !is.null(preds$prob_test)) {
    roc_test <- pROC::roc(test_actual, preds$prob_test, quiet = TRUE, ci = FALSE, smooth = FALSE)
    roc_objects_test[[model_name]] <- roc_test
    auc_test <- as.numeric(pROC::auc(roc_test))
    auc_rows[[length(auc_rows) + 1]] <- c("测试集", model_name, model_type, length(test_actual), test_event_count, auc_test)
  }
}

delong_rows <- list()
model_names <- names(roc_objects_train)
if (length(model_names) < 2) {
  stop("可用模型不足 2 个，无法进行 DeLong 检验。", call. = FALSE)
}

pairwise_delong <- function(roc_list, dataset_label) {
  names <- names(roc_list)
  out <- list()
  if (length(names) < 2) return(out)
  n <- length(roc_list[[1]]$response)
  for (i in seq_along(names)) {
    for (j in seq_along(names)) {
      if (j <= i) next
      a <- names[i]
      b <- names[j]
      roc_a <- roc_list[[a]]
      roc_b <- roc_list[[b]]
      test <- tryCatch(
        pROC::roc.test(roc_a, roc_b, method = "delong", paired = TRUE),
        error = function(e) NULL
      )
      auc_a <- as.numeric(pROC::auc(roc_a))
      auc_b <- as.numeric(pROC::auc(roc_b))
      delta <- auc_a - auc_b
      z_value <- if (!is.null(test)) as.numeric(test$statistic) else NA_real_
      p_value <- if (!is.null(test)) as.numeric(test$p.value) else NA_real_
      out[[length(out) + 1]] <- c(dataset_label, a, b, n, auc_a, auc_b, delta, z_value, p_value, "DeLong")
    }
  }
  out
}

delong_rows <- c(delong_rows, pairwise_delong(roc_objects_train, "训练集"))
if (has_test && length(roc_objects_test) >= 2) {
  delong_rows <- c(delong_rows, pairwise_delong(roc_objects_test, "测试集"))
}

to_plot_df <- function(roc_list, dataset_label) {
  rows <- data.frame()
  for (model_name in names(roc_list)) {
    display_name <- as.character(model_display_map[[model_name]] %||% model_name)
    roc_obj <- roc_list[[model_name]]
    df <- data.frame(
      fpr = 1 - roc_obj$specificities,
      tpr = roc_obj$sensitivities,
      model = display_name,
      dataset = dataset_label,
      stringsAsFactors = FALSE
    )
    df <- df[stats::complete.cases(df[, c("fpr", "tpr")]), , drop = FALSE]
    rows <- rbind(rows, df)
  }
  rows
}

roc_plot_for_dataset <- function(roc_list, path_png, path_pdf, title_text) {
  if (length(roc_list) == 0) {
    return(invisible(NULL))
  }

  plot_df <- to_plot_df(roc_list, "dataset")
  model_order <- unique(plot_df$model)
  auc_map <- list()
  for (model_name in names(roc_list)) {
    display_name <- as.character(model_display_map[[model_name]] %||% model_name)
    auc_map[[display_name]] <- as.numeric(pROC::auc(roc_list[[model_name]]))
  }

  label_map <- vapply(
    model_order,
    function(name) {
      auc_value <- auc_map[[name]]
      if (is.null(auc_value) || is.na(auc_value)) return(name)
      paste0(name, " (AUC=", formatC(as.numeric(auc_value), format = "f", digits = 3), ")")
    },
    character(1)
  )
  names(label_map) <- model_order

  plot_df$model_label <- factor(
    vapply(plot_df$model, function(name) label_map[[name]], character(1)),
    levels = unname(label_map)
  )

  plot_obj <- ggplot(plot_df, aes(x = fpr, y = tpr, color = model_label)) +
    geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "#94a3b8", linewidth = 0.8) +
    geom_line(linewidth = 1.1) +
    coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
    labs(
      title = title_text,
      x = "1 - Specificity",
      y = "Sensitivity",
      color = "Model"
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

  png(filename = path_png, width = 1800, height = 1400, res = 300)
  tryCatch({
    print(plot_obj)
  }, finally = {
    dev.off()
  })
  ggsave(path_pdf, plot_obj, width = 6, height = 4.8, device = cairo_pdf)
}

roc_plot_for_dataset(roc_objects_train, train_plot_path, train_plot_pdf_path, "ROC Curve (Train)")
if (has_test && length(roc_objects_test) > 0) {
  roc_plot_for_dataset(roc_objects_test, test_plot_path, test_plot_pdf_path, "ROC Curve (Test)")
}

note <- paste0(
  "已对 ", length(model_specs), " 个模型进行 AUC 比较；",
  "DeLong 检验采用同一数据集配对检验（paired）。",
  if (has_test) "同时输出训练集与测试集对比。" else "当前无测试集，仅输出训练集对比。"
)

result <- list(
  dataset_name = dataset_name,
  has_test = has_test,
  outcome_variable = outcome,
  event_level = event_level,
  reference_level = reference_level,
  model_count = length(model_specs),
  auc_rows = auc_rows,
  delong_rows = delong_rows,
  note = note
)

jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")
