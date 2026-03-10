backtick <- function(x) paste0("`", gsub("`", "", x, fixed = TRUE), "`")

trim_dataframe_strings <- function(df) {
  for (column_name in names(df)) {
    if (is.character(df[[column_name]])) {
      trimmed <- trimws(df[[column_name]])
      trimmed[trimmed == ""] <- NA
      df[[column_name]] <- trimmed
    }
  }
  df
}

prepare_binary_outcome <- function(df, outcome) {
  outcome_values <- unique(df[[outcome]])
  outcome_values <- outcome_values[!is.na(outcome_values)]
  if (length(outcome_values) != 2) {
    stop("二分类建模要求结局变量恰好有两个水平。", call. = FALSE)
  }

  if (is.numeric(df[[outcome]])) {
    numeric_values <- sort(unique(as.numeric(df[[outcome]])))
    numeric_values <- numeric_values[!is.na(numeric_values)]
    if (length(numeric_values) != 2) {
      stop("数值型二分类结局要求恰好两个水平。", call. = FALSE)
    }
    reference_level <- as.character(numeric_values[1])
    event_level <- as.character(numeric_values[2])
    df[[outcome]] <- factor(as.numeric(df[[outcome]]), levels = numeric_values, labels = c(reference_level, event_level))
    outcome_numeric <- ifelse(df[[outcome]] == event_level, 1, 0)
  } else {
    df[[outcome]] <- factor(df[[outcome]])
    if (nlevels(df[[outcome]]) != 2) {
      stop("二分类建模要求结局变量恰好有两个水平。", call. = FALSE)
    }
    reference_level <- levels(df[[outcome]])[1]
    event_level <- levels(df[[outcome]])[2]
    outcome_numeric <- ifelse(df[[outcome]] == event_level, 1, 0)
  }

  list(
    data = df,
    reference_level = reference_level,
    event_level = event_level,
    outcome_numeric = as.numeric(outcome_numeric)
  )
}

prepare_survival_event <- function(df, event_var) {
  event_values <- unique(df[[event_var]])
  event_values <- event_values[!is.na(event_values)]
  if (length(event_values) != 2) {
    stop("生存分析要求事件变量恰好有两个水平。", call. = FALSE)
  }

  if (is.numeric(df[[event_var]])) {
    numeric_values <- sort(unique(as.numeric(df[[event_var]])))
    numeric_values <- numeric_values[!is.na(numeric_values)]
    if (length(numeric_values) != 2) {
      stop("数值型事件变量要求恰好两个水平。", call. = FALSE)
    }
    reference_level <- as.character(numeric_values[1])
    event_level <- as.character(numeric_values[2])
    df[[event_var]] <- factor(as.numeric(df[[event_var]]), levels = numeric_values, labels = c(reference_level, event_level))
    event_numeric <- ifelse(df[[event_var]] == event_level, 1, 0)
  } else {
    df[[event_var]] <- factor(df[[event_var]])
    if (nlevels(df[[event_var]]) != 2) {
      stop("生存分析要求事件变量恰好有两个水平。", call. = FALSE)
    }
    reference_level <- levels(df[[event_var]])[1]
    event_level <- levels(df[[event_var]])[2]
    event_numeric <- ifelse(df[[event_var]] == event_level, 1, 0)
  }

  list(
    data = df,
    reference_level = reference_level,
    event_level = event_level,
    event_numeric = as.numeric(event_numeric)
  )
}

factorize_predictors <- function(df, predictors, categorical_predictors) {
  valid_predictors <- c()
  for (predictor in predictors) {
    column <- df[[predictor]]
    unique_values <- unique(column[!is.na(column)])
    if (length(unique_values) >= 2) {
      if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {
        df[[predictor]] <- as.factor(column)
      }
      valid_predictors <- c(valid_predictors, predictor)
    }
  }

  list(
    data = df,
    valid_predictors = unique(valid_predictors)
  )
}

parse_mtry_arg <- function(value, predictor_count) {
  text <- tolower(trimws(as.character(value)))
  if (text %in% c("", "sqrt(p)", "sqrt")) {
    return(max(1L, floor(sqrt(predictor_count))))
  }
  if (text %in% c("p/3", "p / 3")) {
    return(max(1L, floor(predictor_count / 3)))
  }
  numeric_value <- suppressWarnings(as.integer(text))
  if (!is.na(numeric_value) && numeric_value >= 1) {
    return(min(as.integer(predictor_count), numeric_value))
  }
  max(1L, floor(sqrt(predictor_count)))
}

compute_binary_metrics <- function(actual, probability, threshold = 0.5) {
  actual <- as.numeric(actual)
  probability <- as.numeric(probability)
  keep <- !is.na(actual) & !is.na(probability)
  actual <- actual[keep]
  probability <- probability[keep]
  n <- length(actual)
  if (n == 0) {
    return(list(
      sample_size = 0L,
      event_count = 0L,
      auc = NA_real_,
      accuracy = NA_real_,
      sensitivity = NA_real_,
      specificity = NA_real_,
      precision = NA_real_,
      npv = NA_real_,
      f1 = NA_real_,
      brier_score = NA_real_
    ))
  }

  predicted <- ifelse(probability >= threshold, 1, 0)
  tp <- sum(predicted == 1 & actual == 1)
  tn <- sum(predicted == 0 & actual == 0)
  fp <- sum(predicted == 1 & actual == 0)
  fn <- sum(predicted == 0 & actual == 1)

  auc_value <- NA_real_
  if (length(unique(actual)) == 2 && requireNamespace("pROC", quietly = TRUE)) {
    auc_value <- tryCatch(
      as.numeric(pROC::auc(actual, probability, quiet = TRUE)),
      error = function(e) NA_real_
    )
  }

  precision <- if ((tp + fp) == 0) NA_real_ else tp / (tp + fp)
  recall <- if ((tp + fn) == 0) NA_real_ else tp / (tp + fn)

  list(
    sample_size = as.integer(n),
    event_count = as.integer(sum(actual == 1)),
    auc = auc_value,
    accuracy = (tp + tn) / n,
    sensitivity = if ((tp + fn) == 0) NA_real_ else tp / (tp + fn),
    specificity = if ((tn + fp) == 0) NA_real_ else tn / (tn + fp),
    precision = precision,
    npv = if ((tn + fn) == 0) NA_real_ else tn / (tn + fn),
    f1 = if (is.na(precision) || is.na(recall) || (precision + recall) == 0) NA_real_ else 2 * precision * recall / (precision + recall),
    brier_score = mean((probability - actual) ^ 2)
  )
}

compute_regression_metrics <- function(actual, predicted) {
  actual <- as.numeric(actual)
  predicted <- as.numeric(predicted)
  keep <- !is.na(actual) & !is.na(predicted)
  actual <- actual[keep]
  predicted <- predicted[keep]
  n <- length(actual)
  if (n == 0) {
    return(list(
      sample_size = 0L,
      rmse = NA_real_,
      mae = NA_real_,
      r_squared = NA_real_
    ))
  }
  rmse <- sqrt(mean((predicted - actual) ^ 2))
  mae <- mean(abs(predicted - actual))
  denom <- sum((actual - mean(actual)) ^ 2)
  r_squared <- if (is.finite(denom) && denom > 0) 1 - sum((actual - predicted) ^ 2) / denom else NA_real_
  list(
    sample_size = as.integer(n),
    rmse = rmse,
    mae = mae,
    r_squared = r_squared
  )
}

prepare_xgb_matrices <- function(train_df, test_df, predictors, categorical_predictors) {
  train_features <- train_df[, predictors, drop = FALSE]
  test_features <- if (!is.null(test_df) && nrow(test_df) > 0) test_df[, predictors, drop = FALSE] else NULL

  combined <- if (is.null(test_features)) train_features else rbind(train_features, test_features)
  if (!is.null(test_features) && nrow(test_features) > 0) {
    source_index <- c(rep("train", nrow(train_features)), rep("test", nrow(test_features)))
  } else {
    source_index <- rep("train", nrow(train_features))
  }

  for (predictor in predictors) {
    column <- combined[[predictor]]
    if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {
      combined[[predictor]] <- as.factor(column)
    }
  }

  design <- stats::model.matrix(~ . - 1, data = combined[, predictors, drop = FALSE])
  train_matrix <- design[source_index == "train", , drop = FALSE]
  test_matrix <- if (any(source_index == "test")) design[source_index == "test", , drop = FALSE] else NULL

  list(
    train_matrix = train_matrix,
    test_matrix = test_matrix,
    feature_names = colnames(train_matrix)
  )
}

compute_survival_concordance <- function(time, event, score) {
  tryCatch(
    {
      result <- survival::concordance(survival::Surv(time, event) ~ score)
      as.numeric(result$concordance)
    },
    error = function(e) NA_real_
  )
}

parse_threshold_range <- function(range_text) {
  text <- trimws(as.character(range_text))
  parts <- unlist(strsplit(gsub("[^0-9.\\-]+", " ", text), "\\s+"))
  parts <- parts[nzchar(parts)]
  numeric_parts <- suppressWarnings(as.numeric(parts))
  numeric_parts <- numeric_parts[!is.na(numeric_parts)]
  if (length(numeric_parts) >= 2) {
    lower <- numeric_parts[1]
    upper <- numeric_parts[2]
  } else {
    lower <- 0.05
    upper <- 0.80
  }
  lower <- max(0.01, min(lower, 0.99))
  upper <- max(lower + 0.01, min(upper, 0.99))
  c(lower, upper)
}
