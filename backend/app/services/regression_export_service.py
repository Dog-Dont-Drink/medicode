from __future__ import annotations

from io import BytesIO
from typing import Any, Literal

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, Side


def _merge_model_frames(
    univariate_rows: list[dict[str, Any]],
    multivariate_rows: list[dict[str, Any]],
    value_key: str,
) -> pd.DataFrame:
    order: list[str] = []
    univariate_map = {str(item.get('term') or ''): item for item in univariate_rows}
    multivariate_map = {str(item.get('term') or ''): item for item in multivariate_rows}

    for item in univariate_rows:
        term = str(item.get('term') or '')
        if term and term not in order:
            order.append(term)
    for item in multivariate_rows:
        term = str(item.get('term') or '')
        if term and term not in order:
            order.append(term)

    merged = []
    for term in order:
        uni = univariate_map.get(term, {})
        multi = multivariate_map.get(term, {})
        merged.append(
            {
                '项': term,
                '单因素 系数': uni.get('coefficient'),
                '单因素 SE': uni.get('std_error'),
                f'单因素 {value_key}': uni.get(value_key),
                '单因素 95% CI': _format_interval(uni.get('conf_low'), uni.get('conf_high')),
                '单因素 P值': _format_p(uni.get('p_value')),
                '多因素 系数': multi.get('coefficient'),
                '多因素 SE': multi.get('std_error'),
                f'多因素 {value_key}': multi.get(value_key),
                '多因素 95% CI': _format_interval(multi.get('conf_low'), multi.get('conf_high')),
                '多因素 P值': _format_p(multi.get('p_value')),
            }
        )
    return pd.DataFrame(merged)


def _build_result_frame(analysis_kind: Literal['linear', 'lasso', 'logistic', 'cox'], payload: dict[str, Any]) -> pd.DataFrame:
    if analysis_kind == 'linear':
        rows = [
            {
                '项': item.get('term'),
                'Estimate': item.get('estimate'),
                'SE': item.get('std_error'),
                't': item.get('statistic'),
                '95% CI': _format_interval(item.get('conf_low'), item.get('conf_high')),
                'P值': _format_p(item.get('p_value')),
            }
            for item in (payload.get('coefficients') or [])
        ]
        return pd.DataFrame(rows)

    if analysis_kind == 'logistic':
        return _merge_model_frames(
            payload.get('univariate_coefficients') or [],
            payload.get('coefficients') or [],
            'odds_ratio',
        )

    if analysis_kind == 'cox':
        return _merge_model_frames(
            payload.get('univariate_coefficients') or [],
            payload.get('coefficients') or [],
            'hazard_ratio',
        )

    rows = [
        {
            '变量': item.get('term'),
            'lambda.min 系数': item.get('coefficient_lambda_min'),
            'lambda.1se 系数': item.get('coefficient_lambda_1se'),
            'lambda.min 入选': '是' if item.get('selected_at_lambda_min') else '否',
            'lambda.1se 入选': '是' if item.get('selected_at_lambda_1se') else '否',
        }
        for item in (payload.get('selected_features') or [])
    ]
    return pd.DataFrame(rows)


def _build_note_frame(analysis_kind: Literal['linear', 'lasso', 'logistic', 'cox'], payload: dict[str, Any]) -> pd.DataFrame:
    notes: list[dict[str, Any]] = [
        {'备注项': '数据集', '备注内容': payload.get('dataset_name')},
        {'备注项': '因变量', '备注内容': payload.get('outcome_variable')},
        {'备注项': '自变量', '备注内容': ', '.join(payload.get('predictor_variables') or [])},
        {'备注项': '样本量', '备注内容': payload.get('sample_size')},
        {'备注项': '排除记录数', '备注内容': payload.get('excluded_rows')},
    ]

    if analysis_kind == 'linear':
        notes.extend(
            [
                {'备注项': 'R²', '备注内容': payload.get('r_squared')},
                {'备注项': 'Adjusted R²', '备注内容': payload.get('adjusted_r_squared')},
                {'备注项': 'Residual SE', '备注内容': payload.get('residual_standard_error')},
                {'备注项': 'Model P', '备注内容': _format_p(payload.get('model_p_value'))},
                {'备注项': 'Formula', '备注内容': payload.get('formula')},
            ]
        )
    elif analysis_kind == 'logistic':
        notes.extend(
            [
                {'备注项': '事件水平', '备注内容': payload.get('event_level')},
                {'备注项': '参考水平', '备注内容': payload.get('reference_level')},
                {'备注项': 'Pseudo R²', '备注内容': payload.get('pseudo_r_squared')},
                {'备注项': 'AIC', '备注内容': payload.get('aic')},
                {'备注项': 'Model P', '备注内容': _format_p(payload.get('model_p_value'))},
                {'备注项': 'Formula', '备注内容': payload.get('formula')},
            ]
        )
    elif analysis_kind == 'cox':
        notes.extend(
            [
                {'备注项': '生存时间', '备注内容': payload.get('time_variable')},
                {'备注项': '事件变量', '备注内容': payload.get('event_variable')},
                {'备注项': '事件数', '备注内容': payload.get('event_count')},
                {'备注项': 'C-index', '备注内容': payload.get('concordance')},
                {'备注项': 'Global PH P', '备注内容': _format_p(payload.get('global_ph_p_value'))},
                {'备注项': 'Likelihood P', '备注内容': _format_p(payload.get('likelihood_ratio_p_value'))},
                {'备注项': 'Formula', '备注内容': payload.get('formula')},
            ]
        )
    else:
        notes.extend(
            [
                {'备注项': 'Family', '备注内容': payload.get('family')},
                {'备注项': 'lambda.min', '备注内容': payload.get('lambda_min')},
                {'备注项': 'lambda.1se', '备注内容': payload.get('lambda_1se')},
                {'备注项': 'nonzero @ lambda.min', '备注内容': payload.get('nonzero_count_lambda_min')},
                {'备注项': 'nonzero @ lambda.1se', '备注内容': payload.get('nonzero_count_lambda_1se')},
            ]
        )

    for index, item in enumerate(payload.get('assumptions') or [], 1):
        notes.append({'备注项': f'说明 {index}', '备注内容': item})

    if payload.get('note'):
        notes.append({'备注项': '备注', '备注内容': payload.get('note')})

    return pd.DataFrame(notes)


def _format_interval(low: Any, high: Any) -> str:
    if low is None or high is None:
        return '-'
    try:
        return f"{float(low):.3f} ~ {float(high):.3f}"
    except (TypeError, ValueError):
        return '-'


def _format_p(value: Any) -> str:
    if value is None:
        return '-'
    try:
        number = float(value)
    except (TypeError, ValueError):
        return '-'
    if number < 0.001:
        return '<0.001'
    return f'{number:.3f}'


def _apply_three_line_style(worksheet, data_columns: int, data_rows: int) -> None:
    top_side = Side(style='thin', color='000000')
    header_font = Font(bold=True)

    for cell in worksheet[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(top=top_side, bottom=top_side)

    for row in range(2, data_rows + 1):
        for cell in worksheet[row]:
            cell.alignment = Alignment(vertical='center')

    for cell in worksheet[data_rows]:
        cell.border = Border(bottom=top_side)

    for column_cells in worksheet.iter_cols(min_col=1, max_col=data_columns):
        max_length = max(len(str(cell.value or '')) for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 4, 40)


def export_regression_excel(analysis_kind: Literal['linear', 'lasso', 'logistic', 'cox'], payload: dict[str, Any]) -> bytes:
    result_frame = _build_result_frame(analysis_kind, payload)
    note_frame = _build_note_frame(analysis_kind, payload)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        sheet_name = 'ResultTable'
        result_frame.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        data_rows = max(len(result_frame.index) + 1, 1)
        data_columns = max(len(result_frame.columns), 1)
        _apply_three_line_style(worksheet, data_columns, data_rows)

        startrow = data_rows + 1
        note_frame.to_excel(writer, index=False, sheet_name=sheet_name, startrow=startrow)
        note_header_row = startrow + 1
        for cell in worksheet[note_header_row]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='left', vertical='center')
        for row in range(note_header_row + 1, note_header_row + len(note_frame.index) + 1):
            for cell in worksheet[row]:
                cell.alignment = Alignment(vertical='top', wrap_text=True)

        if analysis_kind in ['lasso', 'cox']:
            plots = payload.get('plots') or []
            if plots:
                plot_rows = [
                    {
                        '图名': item.get('name'),
                        '文件名': item.get('filename'),
                        '类型': item.get('media_type'),
                    }
                    for item in plots
                ]
                plot_frame = pd.DataFrame(plot_rows)
                plot_frame.to_excel(writer, index=False, sheet_name='Plots')
                plot_sheet = writer.sheets['Plots']
                _apply_three_line_style(plot_sheet, max(len(plot_frame.columns), 1), max(len(plot_frame.index) + 1, 1))

    buffer.seek(0)
    return buffer.read()
