# utils.py
# Utility helpers for formatting, export, validation, and summary calculations.

import streamlit as st
import pandas as pd
import io
from datetime import datetime

def apply_clean_dark_style(df):
    """Apply clean dark theme styling to dataframe"""
    culoare_moale = "#dad4bd"
    culoare_header = "#af7c4c"

    return df.style.set_properties(**{
        'background-color': '#111111',
        'color': culoare_moale,
        'border-color': '#262730',
        'text-align': 'center',
        'font-weight': '300',
        'font-size': '13px'
    }).set_table_styles([{
        'selector': 'th',
        'props': [
            ('background-color', '#1a1c23'),
            ('color', culoare_header),
            ('font-weight', '400'),
            ('border', '1px solid #262730'),
            ('font-size', '12px'),
            ('text-transform', 'uppercase')
        ]
    }])

def add_export_buttons(df, filename, summary=None, orientation='landscape'):
    """Export a pandas DataFrame to an Excel file and present a download button."""
    buffer_xl = io.BytesIO()

    # Copy and normalize data before export.
    # Convert any date-related columns to datetime so Excel formatting works correctly.
    df_export = df.copy()
    for col in df_export.columns:
        if 'data' in col.lower():
            df_export[col] = pd.to_datetime(df_export[col], errors='coerce', format='mixed')

    # Fill missing values so Excel cells are not left as NaN.
    df_export = df_export.fillna(0)

    # Create Excel writer
    with pd.ExcelWriter(buffer_xl, engine='xlsxwriter',
                        engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:

        start_row = 6 if summary else 3
        df_export.to_excel(writer, index=False, sheet_name='Raport', startrow=start_row)

        workbook = writer.book
        worksheet = writer.sheets['Raport']

        # Define formats
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter',
            'fg_color': '#D9D9D9', 'font_color': 'black', 'border': 1
        })
        label_fmt = workbook.add_format({'bold': True, 'align': 'center', 'fg_color': '#F2F2F2', 'border': 1})
        val_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'border': 1, 'num_format': '#,##0'})
        header_fmt = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'fg_color': '#BFBFBF', 'font_color': 'black', 'border': 1
        })
        center_fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        date_fmt = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        # Page setup
        if orientation == 'portrait':
            worksheet.set_portrait()
        else:
            worksheet.set_landscape()
        worksheet.set_paper(9)  # A4
        worksheet.set_margins(0.5, 0.5, 0.5, 0.5)
        worksheet.set_default_row(22)  # inaltime confortabila pentru randuri de date

        # Title
        num_cols = len(df_export.columns)
        last_col_idx = num_cols - 1
        titlu_curat = filename.replace('_', ' ').upper()
        worksheet.merge_range(0, 0, 1, last_col_idx, titlu_curat, title_fmt)

        # Summary section
        if summary:
            worksheet.write('A4', 'TOTAL METRI', label_fmt)
            worksheet.write('A5', summary.get('METRI', 0), val_fmt)
            worksheet.write('B4', 'TOTAL CABLURI', label_fmt)
            worksheet.write('B5', summary.get('CAB', 0), val_fmt)
            worksheet.write('C4', 'TOTAL LISTE', label_fmt)
            worksheet.write('C5', summary.get('LISTE', len(df_export)), val_fmt)

        # Set column widths and write headers.
        min_width = 25 if num_cols <= 5 else 12

        for i, col in enumerate(df_export.columns):
            content_width = max(df_export[col].astype(str).str.len().fillna(0).max(), len(col)) + 4
            actual_width = max(content_width, min_width)
            if actual_width > 50:
                actual_width = 50

            worksheet.set_column(i, i, actual_width)
            worksheet.write(start_row, i, col, header_fmt)

            # Write each cell value with the correct Excel format.
            for row_num, value in enumerate(df_export[col]):
                if pd.api.types.is_datetime64_any_dtype(df_export[col]):
                    if pd.notnull(value):
                        worksheet.write_datetime(start_row + 1 + row_num, i, value, date_fmt)
                    else:
                        worksheet.write(start_row + 1 + row_num, i, "", center_fmt)
                else:
                    worksheet.write(start_row + 1 + row_num, i, value, center_fmt)

        # Filters and freeze
        worksheet.autofilter(start_row, 0, start_row + len(df_export), last_col_idx)
        worksheet.freeze_panes(start_row + 1, 0)

    # Download button
    st.download_button(
        label=f"📥 Descarcă Excel: {filename}",
        data=buffer_xl.getvalue(),
        file_name=f"{filename}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"xl_{filename}_{datetime.now().strftime('%H%M%S')}"
    )

def validate_numeric_input(value_str, field_name):
    """Parse and validate numeric input from text fields."""
    if not value_str.strip():
        raise ValueError(f"{field_name} este obligatoriu")

    try:
        # Allow comma or dot as decimal separator.
        cleaned = value_str.replace(',', '.').strip()
        value = float(cleaned)

        if value <= 0:
            raise ValueError(f"{field_name} trebuie să fie mai mare decât 0")

        return int(value) if value.is_integer() else value
    except ValueError:
        raise ValueError(f"{field_name} trebuie să fie un număr valid")

def format_date_for_display(date_obj):
    """Convert a date object into a human-readable string."""
    if date_obj:
        return date_obj.strftime('%d.%m.%Y')
    return ""

def calculate_summary(df, columns):
    """Build a summary dictionary for selected numeric columns."""
    summary = {}
    for col in columns:
        if col in df.columns:
            if col == 'Lungime':
                summary['METRI'] = int(pd.to_numeric(df[col], errors='coerce').sum())
            elif col == 'Nr Cabluri':
                summary['CAB'] = int(pd.to_numeric(df[col], errors='coerce').sum())
            elif col == 'count':
                summary['LISTE'] = len(df)
    return summary