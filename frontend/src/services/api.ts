import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Attach auth token to requests
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// ========================
// Payment API
// ========================

export interface PaymentCreateRequest {
    packageId: string
}

export interface PaymentCreateResponse {
    orderId: string
    qrCodeUrl: string
    totalAmount: string
    expireTime: string
}

export interface PaymentStatusResponse {
    orderId: string
    status: 'pending' | 'paid' | 'failed' | 'expired'
    paidAt?: string
    resourcesAdded?: number
    tokensAdded?: number
}

export interface OrderRecord {
    orderId: string
    packageName: string
    amount: number
    resources: number
    tokens: number
    status: 'pending' | 'paid' | 'failed' | 'expired'
    createdAt: string
    paidAt?: string
}

export interface PaymentPackage {
    id: string
    name: string
    price: number
    resources: number
    tokens: number
    unitPrice: string
    badge: string
    features: string[]
}

export interface TokenBalanceResponse {
    balance: number
    resource_balance: number
    plan: string
    used_this_month: number
    actual_used_this_month: number
}

export interface PdfDownloadResponse {
    blob: Blob
    remainingResources: number | null
    chargedResources: number | null
}

export interface DatasetItem {
    id: string
    name: string
    file_size: number | null
    file_format: string | null
    row_count: number | null
    column_count: number | null
    created_at: string
}

export interface DatasetPreviewResponse {
    columns: string[]
    rows: Record<string, string | number | boolean | null>[]
    total_rows: number
    total_columns: number
}

export interface DatasetValueFrequency {
    value: string
    count: number
    ratio: number
}

export interface DatasetColumnSummary {
    name: string
    kind: 'numeric' | 'categorical' | 'datetime' | 'boolean'
    kind_source?: 'auto' | 'manual'
    non_null_count: number
    missing_count: number
    missing_rate: number
    unique_count: number
    sample_values: string[]
    numeric_min: number | null
    numeric_max: number | null
    numeric_mean: number | null
    numeric_std: number | null
    numeric_median: number | null
    numeric_q1: number | null
    numeric_q3: number | null
    datetime_min: string | null
    datetime_max: string | null
    top_values: DatasetValueFrequency[] | null
}

export interface DatasetSummaryResponse {
    total_rows: number
    total_columns: number
    numeric_columns: number
    categorical_columns: number
    datetime_columns: number
    boolean_columns: number
    complete_rows: number
    duplicate_rows: number
    missing_cells: number
    missing_rate: number
    columns: DatasetColumnSummary[]
}

export interface DatasetColumnKindUpdateRequest {
    kind: 'auto' | 'con' | 'cat' | 'continuous' | 'categorical' | 'numeric'
}

export interface DatasetColumnKindUpdateResponse {
    column_name: string
    kind: 'numeric' | 'categorical' | 'datetime' | 'boolean'
    kind_source: 'auto' | 'manual'
}

export interface DatasetCleaningRequest {
    outlier_strategy: 'none' | 'clip_iqr' | 'remove_rows'
    outlier_factor: number
    outlier_columns: string[]
    drop_high_missing_columns: boolean
    missing_column_threshold: number
    missing_drop_columns: string[]
    numeric_missing_strategy: 'none' | 'mean' | 'median' | 'multiple_imputation'
    numeric_missing_columns: string[]
    categorical_missing_strategy: 'none' | 'mode' | 'unknown'
    categorical_missing_columns: string[]
    scaling_strategy: 'none' | 'normalize' | 'standardize' | 'center'
    scaling_columns: string[]
    categorical_encoding: 'none' | 'one_hot'
    encoding_columns: string[]
    output_name?: string
}

export interface DatasetCleaningResult {
    dataset: DatasetItem
    original_rows: number
    original_columns: number
    cleaned_rows: number
    cleaned_columns: number
    removed_rows: number
    removed_columns: number
    numeric_imputed_cells: number
    categorical_imputed_cells: number
    encoded_columns_added: number
    operations: string[]
}

export interface TTestRequest {
    dataset_id: string
    group_variable: string
    continuous_variables: string[]
    alpha: number
    confirm_independence: boolean
}

export interface TTestGroupSummary {
    group: string
    n: number
    mean: number | null
    sd: number | null
    median: number | null
    q1: number | null
    q3: number | null
}

export interface TTestNormalityCheck {
    group: string
    n: number
    p_value: number | null
    passed: boolean
    method: string
}

export interface TTestVariableResult {
    variable: string
    group_summaries: TTestGroupSummary[]
    normality_checks: TTestNormalityCheck[]
    variance_test_name: string
    variance_p_value: number | null
    equal_variance: boolean | null
    satisfies_t_test: boolean
    recommended_test: string
    executed_test: string
    statistic: number | null
    df: number | null
    p_value: number | null
    estimate: number | null
    conf_low: number | null
    conf_high: number | null
    note: string
}

export interface TTestResponse {
    dataset_name: string
    group_variable: string
    group_levels: string[]
    alpha: number
    confirm_independence: boolean
    assumptions: string[]
    variables: TTestVariableResult[]
}

export interface AnovaRequest {
    dataset_id: string
    group_variable: string
    continuous_variables: string[]
    alpha: number
    confirm_independence: boolean
}

export interface AnovaVariableResult {
    variable: string
    group_summaries: TTestGroupSummary[]
    normality_checks: TTestNormalityCheck[]
    variance_test_name: string
    variance_p_value: number | null
    equal_variance: boolean | null
    satisfies_anova: boolean
    recommended_test: string
    executed_test: string
    statistic: number | null
    df_between: number | null
    df_within: number | null
    p_value: number | null
    note: string
}

export interface AnovaResponse {
    dataset_name: string
    group_variable: string
    group_levels: string[]
    alpha: number
    confirm_independence: boolean
    assumptions: string[]
    variables: AnovaVariableResult[]
}

export interface ChiSquareRequest {
    dataset_id: string
    group_variable: string
    categorical_variables: string[]
    alpha: number
    confirm_independence: boolean
}

export interface ChiSquareLevelRow {
    level: string
    group_values: string[]
}

export interface ChiSquareVariableResult {
    variable: string
    level_rows: ChiSquareLevelRow[]
    minimum_expected_count: number | null
    expected_count_warning: boolean
    recommended_test: string
    executed_test: string
    statistic: number | null
    df: number | null
    p_value: number | null
    note: string
}

export interface ChiSquareResponse {
    dataset_name: string
    group_variable: string
    group_levels: string[]
    alpha: number
    confirm_independence: boolean
    assumptions: string[]
    variables: ChiSquareVariableResult[]
}

export interface RepeatedMeasuresRequest {
    dataset_id: string
    subject_variable: string
    between_variable?: string | null
    time_variable: string
    continuous_variables: string[]
    alpha: number
    confirm_repeated_design: boolean
}

export interface RepeatedMeasuresEffectResult {
    statistic: number | null
    df_effect: number | null
    df_error: number | null
    p_value: number | null
    corrected: boolean
}

export interface RepeatedMeasuresTimeSummary {
    time_level: string
    group_level: string | null
    n: number
    mean: number | null
    sd: number | null
    median: number | null
    q1: number | null
    q3: number | null
}

export interface RepeatedMeasuresVariableResult {
    variable: string
    complete_subject_count: number
    excluded_subject_count: number
    duplicate_pair_count: number
    residual_normality_statistic: number | null
    residual_normality_p_value: number | null
    residual_normality_passed: boolean
    residual_normality_method: string
    time_sphericity_statistic: number | null
    time_sphericity_p_value: number | null
    time_sphericity_passed: boolean | null
    time_gg_epsilon: number | null
    time_hf_epsilon: number | null
    interaction_sphericity_statistic: number | null
    interaction_sphericity_p_value: number | null
    interaction_sphericity_passed: boolean | null
    interaction_gg_epsilon: number | null
    interaction_hf_epsilon: number | null
    executed_test: string
    note: string
    time_summaries: RepeatedMeasuresTimeSummary[]
    time_effect: RepeatedMeasuresEffectResult
    between_effect: RepeatedMeasuresEffectResult | null
    interaction_effect: RepeatedMeasuresEffectResult | null
}

export interface RepeatedMeasuresResponse {
    dataset_name: string
    subject_variable: string
    between_variable?: string | null
    between_levels: string[]
    time_variable: string
    time_levels: string[]
    alpha: number
    confirm_repeated_design: boolean
    assumptions: string[]
    variables: RepeatedMeasuresVariableResult[]
}

export interface LinearRegressionRequest {
    dataset_id: string
    outcome_variable: string
    predictor_variables: string[]
    alpha: number
}

export interface LinearRegressionCoefficient {
    term: string
    estimate: number | null
    std_error: number | null
    statistic: number | null
    p_value: number | null
    conf_low: number | null
    conf_high: number | null
}

export interface LinearRegressionResponse {
    dataset_name: string
    outcome_variable: string
    predictor_variables: string[]
    sample_size: number
    excluded_rows: number
    alpha: number
    r_squared: number | null
    adjusted_r_squared: number | null
    residual_standard_error: number | null
    f_statistic: number | null
    df_model: number | null
    df_residual: number | null
    model_p_value: number | null
    formula: string
    assumptions: string[]
    residual_normality_method: string
    residual_normality_p_value: number | null
    residual_normality_passed: boolean
    homoscedasticity_test_method: string
    homoscedasticity_p_value: number | null
    homoscedasticity_passed: boolean
    coefficients: LinearRegressionCoefficient[]
    plots: LassoPlotPayload[]
    note: string
}

export interface LogisticRegressionRequest {
    dataset_id: string
    outcome_variable: string
    predictor_variables: string[]
    alpha: number
}

export interface LogisticRegressionCoefficient {
    term: string
    coefficient: number | null
    odds_ratio: number | null
    std_error: number | null
    z_value: number | null
    p_value: number | null
    conf_low: number | null
    conf_high: number | null
}

export interface LogisticRegressionResponse {
    dataset_name: string
    outcome_variable: string
    event_level: string
    reference_level: string
    predictor_variables: string[]
    sample_size: number
    excluded_rows: number
    alpha: number
    pseudo_r_squared: number | null
    aic: number | null
    null_deviance: number | null
    residual_deviance: number | null
    df_model: number | null
    df_residual: number | null
    model_p_value: number | null
    formula: string
    assumptions: string[]
    univariate_coefficients: LogisticRegressionCoefficient[]
    coefficients: LogisticRegressionCoefficient[]
    plots: LassoPlotPayload[]
    note: string
}

export interface LassoRegressionRequest {
    dataset_id: string
    outcome_variable: string
    predictor_variables: string[]
    alpha: number
    nfolds: number
}

export interface LassoFeatureResult {
    term: string
    coefficient_lambda_min: number | null
    coefficient_lambda_1se: number | null
    selected_at_lambda_min: boolean
    selected_at_lambda_1se: boolean
}

export interface LassoPlotPayload {
    name: string
    filename: string
    media_type: string
    content_base64: string
    vector_pdf_filename?: string | null
    vector_pdf_base64?: string | null
}

export interface LassoRegressionResponse {
    dataset_name: string
    outcome_variable: string
    predictor_variables: string[]
    family: 'gaussian' | 'binomial'
    event_level?: string | null
    reference_level?: string | null
    sample_size: number
    excluded_rows: number
    alpha: number
    lambda_min: number
    lambda_1se: number
    nonzero_count_lambda_min: number
    nonzero_count_lambda_1se: number
    assumptions: string[]
    selected_features: LassoFeatureResult[]
    plots: LassoPlotPayload[]
    note: string
}

export interface CoxRegressionRequest {
    dataset_id: string
    time_variable: string
    event_variable: string
    predictor_variables: string[]
    alpha: number
}

export interface CoxRegressionCoefficient {
    term: string
    coefficient: number | null
    hazard_ratio: number | null
    std_error: number | null
    z_value: number | null
    p_value: number | null
    conf_low: number | null
    conf_high: number | null
}

export interface CoxRegressionPhTest {
    term: string
    statistic: number | null
    df: number | null
    p_value: number | null
}

export interface CoxRegressionResponse {
    dataset_name: string
    time_variable: string
    event_variable: string
    event_level: string
    reference_level: string
    predictor_variables: string[]
    sample_size: number
    event_count: number
    excluded_rows: number
    alpha: number
    concordance: number | null
    concordance_std_error: number | null
    likelihood_ratio_statistic: number | null
    likelihood_ratio_df: number | null
    likelihood_ratio_p_value: number | null
    wald_statistic: number | null
    wald_df: number | null
    wald_p_value: number | null
    score_statistic: number | null
    score_df: number | null
    score_p_value: number | null
    global_ph_p_value: number | null
    formula: string
    assumptions: string[]
    univariate_coefficients: CoxRegressionCoefficient[]
    coefficients: CoxRegressionCoefficient[]
    proportional_hazards_tests: CoxRegressionPhTest[]
    plots: LassoPlotPayload[]
    note: string
}

export interface RegressionInterpretRequest {
    dataset_id: string
    analysis_kind: 'linear' | 'lasso' | 'logistic' | 'cox'
    language?: 'zh' | 'en'
    payload: Record<string, unknown>
}

export interface ClinicalWorkflowNodeRequest {
    id: string
    module_id: string
    label: string
    stage_id: string
    values: Record<string, string>
}

export interface SavedClinicalWorkflowNode {
    id: string
    module_id: string
    label: string
    description?: string | null
    stage_id: string
    values: Record<string, string>
    x: number
    y: number
    order: number
}

export interface SavedClinicalWorkflowConnection {
    id: string
    from_node_id: string
    to_node_id: string
    output_port_id?: string | null
}

export interface ClinicalWorkflowSaveRequest {
    project_id: string
    name: string
    description?: string | null
    workflow_kind?: string
    nodes: SavedClinicalWorkflowNode[]
    connections: SavedClinicalWorkflowConnection[]
}

export interface ClinicalWorkflowUpdateRequest {
    name: string
    description?: string | null
    nodes: SavedClinicalWorkflowNode[]
    connections: SavedClinicalWorkflowConnection[]
}

export interface ClinicalWorkflowSummaryResponse {
    id: string
    project_id: string
    name: string
    description?: string | null
    workflow_kind: string
    node_count: number
    connection_count: number
    created_at: string
    updated_at: string
}

export interface ClinicalWorkflowDetailResponse extends ClinicalWorkflowSummaryResponse {
    nodes: SavedClinicalWorkflowNode[]
    connections: SavedClinicalWorkflowConnection[]
}

export interface ClinicalWorkflowValidationIssue {
    severity: 'error' | 'warning'
    code: string
    message: string
    node_id?: string | null
    connection_id?: string | null
}

export interface ClinicalWorkflowValidationRequest {
    project_id: string
    workflow_kind?: string
    nodes: SavedClinicalWorkflowNode[]
    connections: SavedClinicalWorkflowConnection[]
}

export interface ClinicalWorkflowValidationResponse {
    is_valid: boolean
    issues: ClinicalWorkflowValidationIssue[]
    root_node_ids: string[]
    leaf_node_ids: string[]
}

export interface ClinicalPipelineRunRequest {
    project_id: string
    dataset_id: string
    workflow_id?: string | null
    template_kind: 'binary' | 'survival'
    outcome_variable?: string | null
    time_variable?: string | null
    event_variable?: string | null
    predictor_variables: string[]
    alpha?: number
    nfolds?: number
    workflow_nodes: ClinicalWorkflowNodeRequest[]
    workflow_connections?: SavedClinicalWorkflowConnection[]
    skip_completed?: boolean
}

export interface ClinicalPipelineNodeResult {
    node_id: string
    module_id: string
    label: string
    stage_id: string
    status: 'completed' | 'configured' | 'unsupported' | 'skipped' | 'failed'
    message: string
    details: string[]
    input_snapshot: Record<string, unknown>
    output_summary: Record<string, unknown>
    output_tables: Array<{ name: string; columns: string[]; rows: Array<Array<string | number | boolean | null>> }>
    output_plots: Array<Record<string, unknown>>
    artifacts: ClinicalPipelineArtifactResult[]
    logs: string[]
    next_dataset_ref?: string | null
    next_variable_set: string[]
    created_at?: string | null
}

export interface ClinicalPipelineArtifactResult {
    id?: string | null
    artifact_type: string
    name: string
    filename?: string | null
    media_type?: string | null
    storage_key?: string | null
    payload: Record<string, unknown>
}

export interface ClinicalPipelineDatasetState {
    dataset_name: string
    original_rows: number
    original_columns: number
    analysis_rows: number
    analysis_columns: number
    cleaning_operations: string[]
    summary: DatasetSummaryResponse
}

export interface ClinicalPipelineRunResponse {
    run_id?: string | null
    template_kind: 'binary' | 'survival' | 'continuous'
    dataset_id: string
    dataset_state: ClinicalPipelineDatasetState
    final_predictors: string[]
    node_results: ClinicalPipelineNodeResult[]
    logs: string[]
    engine_notes: string[]
    lasso_result: LassoRegressionResponse | null
    logistic_result: LogisticRegressionResponse | null
    cox_result: CoxRegressionResponse | null
}

export interface ClinicalPipelineRunSummaryResponse {
    run_id: string
    project_id: string
    dataset_id: string
    workflow_id?: string | null
    template_kind: 'binary' | 'survival' | 'continuous'
    status: string
    final_predictor_count: number
    node_count: number
    artifact_count: number
    created_at: string
    completed_at?: string | null
}

export interface ClinicalPipelineRunDetailResponse extends ClinicalPipelineRunResponse {
    project_id: string
    workflow_id?: string | null
    status: string
    created_at: string
    completed_at?: string | null
    request_payload: Record<string, unknown>
}

export interface ClinicalPipelineNodeDetailResponse extends ClinicalPipelineNodeResult {
    run_id: string
    execution_order: number
    created_at: string
}

export interface RegressionExportRequest {
    analysis_kind: 'linear' | 'lasso' | 'logistic' | 'cox'
    payload: Record<string, unknown>
}

export interface LassoPlotPdfExportRequest {
    dataset_id: string
    plot: LassoPlotPayload
}

export interface RegressionInterpretResponse {
    feature_name: string
    analysis_kind: 'linear' | 'lasso' | 'logistic' | 'cox'
    language: 'zh' | 'en'
    model: string
    content: string
    analysis_id?: string | null
    saved_at?: string | null
    llm_tokens_used: number
    charged_resources: number
    charged_tokens: number
    remaining_resources: number
    remaining_balance: number
}

export interface SavedRegressionInterpretResponse {
    found: boolean
    feature_name?: string | null
    analysis_kind?: 'linear' | 'lasso' | 'logistic' | 'cox' | null
    language?: 'zh' | 'en' | null
    model?: string | null
    content?: string | null
    analysis_id?: string | null
    saved_at?: string | null
    llm_tokens_used: number
    charged_resources: number
    charged_tokens: number
}

export interface TableOneRequest {
    dataset_id: string
    group_variable: string
    variables: string[]
    decimals?: number
}

export interface TableOneResponse {
    title: string
    dataset_name: string
    group_variable: string
    group_levels: string[]
    headers: string[]
    rows: string[][]
    continuous_variables: string[]
    categorical_variables: string[]
    nonnormal_variables: string[]
    normality_method: string
}

export interface TableOneInterpretRequest {
    dataset_id: string
    language: 'zh' | 'en'
    table: TableOneResponse
}

export interface TableOneInterpretResponse {
    feature_name: string
    language: 'zh' | 'en'
    model: string
    content: string
    analysis_id?: string | null
    saved_at?: string | null
    llm_tokens_used: number
    charged_resources: number
    charged_tokens: number
    remaining_resources: number
    remaining_balance: number
}

export interface SavedTableOneInterpretResponse {
    found: boolean
    feature_name?: string | null
    language?: 'zh' | 'en' | null
    model?: string | null
    content?: string | null
    analysis_id?: string | null
    saved_at?: string | null
    llm_tokens_used: number
    charged_resources: number
    charged_tokens: number
}

export interface ReportListItem {
    analysis_id: string
    name: string
    analysis_type: string
    status: string
    project_id: string
    project_name: string
    dataset_id?: string | null
    dataset_name?: string | null
    feature_name?: string | null
    language?: 'zh' | 'en' | null
    model?: string | null
    group_variable?: string | null
    content?: string | null
    prompt_tokens: number
    completion_tokens: number
    actual_tokens: number
    billed_tokens: number
    created_at: string
    executed_at?: string | null
}

export interface AdminOverviewMetric {
    label: string
    value: number | string
    hint?: string | null
}

export interface AdminDailyMetric {
    date: string
    users: number
    token_consumed: number
}

export interface AdminDashboardResponse {
    overview: AdminOverviewMetric[]
    daily_metrics: AdminDailyMetric[]
    recent_signups: number
    today_token_consumed: number
    today_actual_token_consumed: number
    paid_orders_total: string
}

export interface AdminUserItem {
    id: string
    name: string
    email: string
    role: 'user' | 'admin'
    subscription: string
    token_balance: number
    is_verified: boolean
    is_active: boolean
    institution?: string | null
    title?: string | null
    created_at: string
    last_login_at?: string | null
    project_count: number
    dataset_count: number
    billed_tokens_this_month: number
    actual_tokens_this_month: number
}

export interface AdminUserUpdateRequest {
    name?: string
    email?: string
    role?: 'user' | 'admin'
    subscription?: string
    token_balance?: number
    is_active?: boolean
    is_verified?: boolean
    institution?: string
    title?: string
}

export interface AdminTableInfo {
    name: string
    label: string
    row_count: number
}

export interface AdminTableListResponse {
    tables: AdminTableInfo[]
}

export interface AdminTableColumn {
    name: string
    type: string
    nullable: boolean
    primary_key: boolean
}

export interface AdminTableRowsResponse {
    table_name: string
    primary_key: string
    columns: AdminTableColumn[]
    rows: Record<string, any>[]
    total: number
}

/**
 * Create a payment order (calls alipay.trade.precreate on backend)
 */
export async function createPayment(data: PaymentCreateRequest): Promise<PaymentCreateResponse> {
    const res = await apiClient.post('/api/v1/payment/precreate', data)
    return res.data
}

export async function getPaymentPackages(): Promise<PaymentPackage[]> {
    const res = await apiClient.get('/api/v1/payment/packages')
    return res.data
}

/**
 * Query order payment status
 */
export async function queryPaymentStatus(orderId: string): Promise<PaymentStatusResponse> {
    const res = await apiClient.get(`/api/v1/payment/query/${orderId}`)
    return res.data
}

/**
 * Get user's order history
 */
export async function getOrderHistory(): Promise<OrderRecord[]> {
    const res = await apiClient.get('/api/v1/payment/orders')
    return res.data
}

/**
 * Get current token balance
 */
export async function getTokenBalance(): Promise<TokenBalanceResponse> {
    const res = await apiClient.get('/api/v1/users/balance')
    return res.data
}

// ========================
// Dashboard API
// ========================
export async function getDashboardData() {
    const res = await apiClient.get('/api/v1/dashboard')
    return res.data
}

// ========================
// Users API
// ========================
export async function getUserProfile() {
    const res = await apiClient.get('/api/v1/users/profile')
    return res.data
}

export async function updateUserProfile(data: any) {
    const res = await apiClient.put('/api/v1/users/profile', data)
    return res.data
}

export async function uploadAvatar(data: FormData) {
    const res = await apiClient.post('/api/v1/users/avatar', data, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
    return res.data
}

export async function changePassword(data: any) {
    const res = await apiClient.post('/api/v1/users/change-password', data)
    return res.data
}

// ========================
// Projects API
// ========================
export async function getProjects() {
    const res = await apiClient.get('/api/v1/projects')
    return res.data
}

export async function getProject(projectId: string) {
    const res = await apiClient.get(`/api/v1/projects/${projectId}`)
    return res.data
}

export async function createProject(data: any) {
    const res = await apiClient.post('/api/v1/projects', data)
    return res.data
}

export async function updateProject(projectId: string, data: { name?: string; description?: string; status?: string }) {
    const res = await apiClient.put(`/api/v1/projects/${projectId}`, data)
    return res.data
}

export async function deleteProject(projectId: string) {
    const res = await apiClient.delete(`/api/v1/projects/${projectId}`)
    return res.data
}

// ========================
// Datasets API
// ========================
export async function getDatasets(projectId: string) {
    const res = await apiClient.get('/api/v1/datasets', { params: { project_id: projectId } })
    return res.data as DatasetItem[]
}

export async function uploadDataset(
    data: FormData,
    onProgress?: (loaded: number, total?: number) => void,
) {
    const res = await apiClient.post('/api/v1/datasets/upload', data, {
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (event) => {
            onProgress?.(event.loaded, event.total)
        },
    })
    return res.data as DatasetItem
}

export async function getDatasetPreview(datasetId: string, rows = 5) {
    const res = await apiClient.get(`/api/v1/datasets/${datasetId}/preview`, {
        params: { rows }
    })
    return res.data as DatasetPreviewResponse
}

export async function getDatasetSummary(datasetId: string) {
    const res = await apiClient.get(`/api/v1/datasets/${datasetId}/summary`)
    return res.data as DatasetSummaryResponse
}

export async function updateDatasetColumnKind(datasetId: string, columnName: string, data: DatasetColumnKindUpdateRequest) {
    const encodedColumn = encodeURIComponent(columnName)
    const res = await apiClient.put(`/api/v1/datasets/${datasetId}/columns/${encodedColumn}/kind`, data)
    return res.data as DatasetColumnKindUpdateResponse
}

export async function cleanDataset(datasetId: string, data: DatasetCleaningRequest) {
    const res = await apiClient.post(`/api/v1/datasets/${datasetId}/clean`, data)
    return res.data as DatasetCleaningResult
}

export async function downloadDataset(datasetId: string) {
    const res = await apiClient.get(`/api/v1/datasets/${datasetId}/download`, {
        responseType: 'blob',
    })
    return res.data as Blob
}

export async function generateTableOne(data: TableOneRequest) {
    const res = await apiClient.post('/api/v1/descriptive/table1', data)
    return res.data as TableOneResponse
}

export async function runTTest(data: TTestRequest) {
    const res = await apiClient.post('/api/v1/descriptive/ttest', data)
    return res.data as TTestResponse
}

export async function runAnova(data: AnovaRequest) {
    const res = await apiClient.post('/api/v1/descriptive/anova', data)
    return res.data as AnovaResponse
}

export async function runChiSquare(data: ChiSquareRequest) {
    const res = await apiClient.post('/api/v1/descriptive/chisquare', data)
    return res.data as ChiSquareResponse
}

export async function runRepeatedMeasuresAnova(data: RepeatedMeasuresRequest) {
    const res = await apiClient.post('/api/v1/descriptive/repeated-measures-anova', data)
    return res.data as RepeatedMeasuresResponse
}

export async function runLinearRegression(data: LinearRegressionRequest) {
    const res = await apiClient.post('/api/v1/descriptive/linear-regression', data)
    return res.data as LinearRegressionResponse
}

export async function runLogisticRegression(data: LogisticRegressionRequest) {
    const res = await apiClient.post('/api/v1/descriptive/logistic-regression', data)
    return res.data as LogisticRegressionResponse
}

export async function runLassoRegression(data: LassoRegressionRequest) {
    const res = await apiClient.post('/api/v1/descriptive/lasso-regression', data)
    return res.data as LassoRegressionResponse
}

export async function runCoxRegression(data: CoxRegressionRequest) {
    const res = await apiClient.post('/api/v1/descriptive/cox-regression', data)
    return res.data as CoxRegressionResponse
}

export async function runClinicalPipeline(data: ClinicalPipelineRunRequest) {
    const res = await apiClient.post('/api/v1/advanced-analysis/clinical-pipeline/run', data)
    return res.data as ClinicalPipelineRunResponse
}

export async function listClinicalPipelineRuns(projectId: string, workflowId?: string) {
    const res = await apiClient.get('/api/v1/advanced-analysis/runs', {
        params: {
            project_id: projectId,
            workflow_id: workflowId || undefined,
        },
    })
    return res.data as ClinicalPipelineRunSummaryResponse[]
}

export async function getClinicalPipelineRun(runId: string) {
    const res = await apiClient.get(`/api/v1/advanced-analysis/runs/${runId}`)
    return res.data as ClinicalPipelineRunDetailResponse
}

export async function getClinicalPipelineRunNode(runId: string, nodeId: string) {
    const res = await apiClient.get(`/api/v1/advanced-analysis/runs/${runId}/nodes/${encodeURIComponent(nodeId)}`)
    return res.data as ClinicalPipelineNodeDetailResponse
}

export async function downloadClinicalPipelineArtifact(artifactId: string) {
    const res = await apiClient.get(`/api/v1/advanced-analysis/artifacts/${artifactId}/download`, {
        responseType: 'blob',
    })
    return {
        blob: res.data as Blob,
        contentType: res.headers['content-type'] as string | undefined,
    }
}

export async function listClinicalWorkflows(projectId: string, workflowKind?: string) {
    const res = await apiClient.get('/api/v1/advanced-analysis/workflows', {
        params: { project_id: projectId, workflow_kind: workflowKind || undefined },
    })
    return res.data as ClinicalWorkflowSummaryResponse[]
}

export async function getClinicalWorkflow(workflowId: string) {
    const res = await apiClient.get(`/api/v1/advanced-analysis/workflows/${workflowId}`)
    return res.data as ClinicalWorkflowDetailResponse
}

export async function saveClinicalWorkflow(data: ClinicalWorkflowSaveRequest) {
    const res = await apiClient.post('/api/v1/advanced-analysis/workflows', data)
    return res.data as ClinicalWorkflowDetailResponse
}

export async function updateClinicalWorkflow(workflowId: string, data: ClinicalWorkflowUpdateRequest) {
    const res = await apiClient.put(`/api/v1/advanced-analysis/workflows/${workflowId}`, data)
    return res.data as ClinicalWorkflowDetailResponse
}

export async function validateClinicalWorkflow(data: ClinicalWorkflowValidationRequest) {
    const res = await apiClient.post('/api/v1/advanced-analysis/workflows/validate', data)
    return res.data as ClinicalWorkflowValidationResponse
}

export async function deleteClinicalWorkflow(workflowId: string) {
    const res = await apiClient.delete(`/api/v1/advanced-analysis/workflows/${workflowId}`)
    return res.data as { success: boolean }
}

export async function downloadTableOneExcel(data: TableOneRequest) {
    const res = await apiClient.post('/api/v1/descriptive/table1/export', data, {
        responseType: 'blob',
    })
    return res.data as Blob
}

export async function interpretTableOne(data: TableOneInterpretRequest) {
    const res = await apiClient.post('/api/v1/descriptive/table1/interpret', data)
    return res.data as TableOneInterpretResponse
}

export async function getSavedTableOneInterpretation(data: TableOneInterpretRequest) {
    const res = await apiClient.post('/api/v1/descriptive/table1/interpret/saved', data)
    return res.data as SavedTableOneInterpretResponse
}

export async function interpretRegression(data: RegressionInterpretRequest) {
    const res = await apiClient.post('/api/v1/descriptive/regression/interpret', data)
    return res.data as RegressionInterpretResponse
}

export async function getSavedRegressionInterpretation(data: RegressionInterpretRequest) {
    const res = await apiClient.post('/api/v1/descriptive/regression/interpret/saved', data)
    return res.data as SavedRegressionInterpretResponse
}

export async function downloadRegressionExcel(data: RegressionExportRequest) {
    const res = await apiClient.post('/api/v1/descriptive/regression/export', data, {
        responseType: 'blob',
    })
    return res.data as Blob
}

export async function downloadLassoPlotPdf(data: LassoPlotPdfExportRequest) {
    const res = await apiClient.post('/api/v1/descriptive/lasso-regression/plot/pdf', data, {
        responseType: 'blob',
    })
    return {
        blob: res.data as Blob,
        remainingResources: Number(res.headers['x-resource-balance'] || '') || null,
        chargedResources: Number(res.headers['x-resource-charge'] || '') || null,
    } as PdfDownloadResponse
}

// ========================
// Writing polish (grammar)
// ========================

export type PolishTextType = 'sentence' | 'paragraph' | 'full'
export type PolishSectionType = 'Abstract' | 'Introduction' | 'Methods' | 'Results' | 'Discussion' | 'Other'
export type PolishStrength = 'conservative' | 'standard' | 'deep'

export interface GrammarDocumentCreateRequest {
    title: string
    raw_text: string
    text_type: PolishTextType
    section_type: PolishSectionType
}

export interface GrammarVersion {
    id: string
    version_no: number
    source_module: string
    settings?: Record<string, unknown> | null
    model?: string | null
    llm_tokens_used: number
    created_at: string
}

export interface GrammarDocumentDetail {
    id: string
    title: string
    raw_text: string
    text_type: PolishTextType
    section_type: PolishSectionType
    versions: GrammarVersion[]
}

export interface GrammarEdit {
    id: string
    sentence_index: number
    original_text: string
    revised_text: string
    edit_types: string[]
    reasons: string[]
    confidence: number | null
    changed: boolean
    accepted: boolean | null
}

export interface GrammarPolishRequest {
    raw_text: string
    text_type: PolishTextType
    section_type: PolishSectionType
    strength: PolishStrength
    protect_terms: boolean
    preserve_structure: boolean
}

export interface GrammarPolishResponse {
    document_id: string
    version: GrammarVersion
    revised_text: string
    edits: GrammarEdit[]
    summary: Record<string, unknown>
    charged_resources: number
    charged_tokens: number
    resource_balance: number | null
}

export async function createGrammarDocument(data: GrammarDocumentCreateRequest) {
    const res = await apiClient.post('/api/v1/polish/grammar/documents', data)
    return res.data as GrammarDocumentDetail
}

export async function getGrammarDocument(documentId: string) {
    const res = await apiClient.get(`/api/v1/polish/grammar/documents/${documentId}`)
    return res.data as GrammarDocumentDetail
}

export async function runGrammarPolish(documentId: string, data: GrammarPolishRequest) {
    const res = await apiClient.post(`/api/v1/polish/grammar/documents/${documentId}/polish`, data)
    return res.data as GrammarPolishResponse
}

export async function getGrammarVersion(documentId: string, versionNo: number) {
    const res = await apiClient.get(`/api/v1/polish/grammar/documents/${documentId}/versions/${versionNo}`)
    return res.data as GrammarPolishResponse
}

export async function decideGrammarEdit(editId: string, accepted: boolean) {
    const res = await apiClient.patch(`/api/v1/polish/grammar/edits/${editId}`, { accepted })
    return res.data as GrammarEdit
}

export async function parseGrammarUpload(file: File) {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post('/api/v1/polish/grammar/parse-upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data as { filename: string; text: string }
}

export async function exportGrammarDocument(
    documentId: string,
    versionNo: number,
    fmt: 'docx' | 'md' | 'txt',
    applyAcceptance = true,
) {
    const res = await apiClient.post(`/api/v1/polish/grammar/documents/${documentId}/export`, null, {
        params: { version_no: versionNo, fmt, apply_acceptance: applyAcceptance },
        responseType: 'blob',
    })
    const contentDisposition = res.headers['content-disposition'] as string | undefined
    return { blob: res.data as Blob, contentDisposition }
}

export async function downloadLinearPlotPdf(data: LassoPlotPdfExportRequest) {
    const res = await apiClient.post('/api/v1/descriptive/linear-regression/plot/pdf', data, {
        responseType: 'blob',
    })
    return {
        blob: res.data as Blob,
        remainingResources: Number(res.headers['x-resource-balance'] || '') || null,
        chargedResources: Number(res.headers['x-resource-charge'] || '') || null,
    } as PdfDownloadResponse
}

export async function downloadLogisticPlotPdf(data: LassoPlotPdfExportRequest) {
    const res = await apiClient.post('/api/v1/descriptive/logistic-regression/plot/pdf', data, {
        responseType: 'blob',
    })
    return {
        blob: res.data as Blob,
        remainingResources: Number(res.headers['x-resource-balance'] || '') || null,
        chargedResources: Number(res.headers['x-resource-charge'] || '') || null,
    } as PdfDownloadResponse
}

export async function downloadCoxPlotPdf(data: LassoPlotPdfExportRequest) {
    const res = await apiClient.post('/api/v1/descriptive/cox-regression/plot/pdf', data, {
        responseType: 'blob',
    })
    return {
        blob: res.data as Blob,
        remainingResources: Number(res.headers['x-resource-balance'] || '') || null,
        chargedResources: Number(res.headers['x-resource-charge'] || '') || null,
    } as PdfDownloadResponse
}

export async function getReports() {
    const res = await apiClient.get('/api/v1/reports')
    return res.data as ReportListItem[]
}

export async function deleteReport(analysisId: string) {
    const res = await apiClient.delete(`/api/v1/reports/${analysisId}`)
    return res.data as { success: boolean }
}

export async function getAdminDashboard() {
    const res = await apiClient.get('/api/v1/admin/dashboard')
    return res.data as AdminDashboardResponse
}

export async function getAdminUsers() {
    const res = await apiClient.get('/api/v1/admin/users')
    return res.data as AdminUserItem[]
}

export async function updateAdminUser(userId: string, data: AdminUserUpdateRequest) {
    const res = await apiClient.put(`/api/v1/admin/users/${userId}`, data)
    return res.data as AdminUserItem
}

export async function getAdminTables() {
    const res = await apiClient.get('/api/v1/admin/tables')
    return res.data as AdminTableListResponse
}

export async function getAdminTableRows(tableName: string, limit = 50) {
    const res = await apiClient.get(`/api/v1/admin/tables/${tableName}`, { params: { limit } })
    return res.data as AdminTableRowsResponse
}

export async function updateAdminTableRow(tableName: string, rowId: string, values: Record<string, any>) {
    const res = await apiClient.put(`/api/v1/admin/tables/${tableName}/rows/${rowId}`, { values })
    return res.data as { success: boolean; row: Record<string, any> }
}

export async function deleteAdminTableRow(tableName: string, rowId: string) {
    const res = await apiClient.delete(`/api/v1/admin/tables/${tableName}/rows/${rowId}`)
    return res.data as { success: boolean }
}

export async function deleteDataset(datasetId: string) {
    const res = await apiClient.delete(`/api/v1/datasets/${datasetId}`)
    return res.data as { success: boolean }
}

export default apiClient
