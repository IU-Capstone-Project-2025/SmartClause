"""
Export Service for Analysis Results

Handles generation of PDF, CSV, and JSON exports from analysis data.
"""

import io
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from jinja2 import Environment, DictLoader
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    HTML = CSS = FontConfiguration = None
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting analysis results in various formats"""
    
    def __init__(self):
        self.jinja_env = Environment(loader=DictLoader(self._get_templates()))
        self.font_config = FontConfiguration() if WEASYPRINT_AVAILABLE else None
    

    def export_analysis_pdf(self, analysis_data: Dict[str, Any]) -> bytes:
        """
        Export analysis as PDF report
        
        Args:
            analysis_data: Analysis results dictionary
            
        Returns:
            PDF bytes
        """
        if not WEASYPRINT_AVAILABLE:
            raise ValueError("WeasyPrint is not available. Please install weasyprint to enable PDF export.")
            
        try:
            # Prepare template data
            template_data = self._prepare_template_data(analysis_data)
            
            # Render HTML
            template = self.jinja_env.get_template('analysis_report')
            html_content = template.render(**template_data)
            
            # Generate PDF
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=self._get_pdf_styles(), font_config=self.font_config)
            
            pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc], font_config=self.font_config)
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            raise ValueError(f"Failed to export PDF: {e}")
    
    def _prepare_template_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        
        # Calculate summary statistics
        document_points = analysis_data.get('document_points', [])
        total_issues = sum(len(point.get('analysis_points', [])) for point in document_points)
        
        # Categorize risks
        risk_counts = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        
        for point in document_points:
            for analysis_point in point.get('analysis_points', []):
                risk = analysis_point.get('risk', '').lower()
                if 'высокий' in risk or 'high' in risk:
                    risk_counts['high'] += 1
                elif 'средний' in risk or 'medium' in risk:
                    risk_counts['medium'] += 1
                elif 'низкий' in risk or 'low' in risk:
                    risk_counts['low'] += 1
                else:
                    risk_counts['unknown'] += 1
        
        document_metadata = analysis_data.get('document_metadata', {})
        
        return {
            'analysis_timestamp': analysis_data.get('analysis_timestamp', ''),
            'document_metadata': document_metadata,
            'total_points': len(document_points),
            'total_issues': total_issues,
            'risk_counts': risk_counts,
            'document_points': document_points,
            'generation_timestamp': datetime.now().strftime('%d.%m.%Y')
        }
    
    def _get_templates(self) -> Dict[str, str]:
        """Get Jinja2 templates for PDF generation"""
        
        analysis_report_template = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчёт о правовом анализе</title>
</head>
<body>
    <div class="header">
        <h1>Отчёт о правовом анализе документа</h1>
        <div class="document-info">
            <p class="timestamp">Создан: {{ generation_timestamp }}</p>
        </div>
    </div>
    
    <div class="summary">
        <h2>Краткий обзор</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <span class="number">{{ total_points }}</span>
                <span class="label">Пунктов документа</span>
            </div>
            <div class="summary-item">
                <span class="number">{{ total_issues }}</span>
                <span class="label">Найдено проблем</span>
            </div>
            <div class="summary-item risk-high">
                <span class="number">{{ risk_counts.high }}</span>
                <span class="label">Высокий риск</span>
            </div>
            <div class="summary-item risk-medium">
                <span class="number">{{ risk_counts.medium }}</span>
                <span class="label">Средний риск</span>
            </div>
            <div class="summary-item risk-low">
                <span class="number">{{ risk_counts.low }}</span>
                <span class="label">Низкий риск</span>
            </div>
        </div>
    </div>
    
    <div class="analysis-details">
        <h2>Подробный анализ</h2>
        
        {% for point in document_points %}
        <div class="document-point">
            <div class="point-header">
                <h3>{{ point.point_number }}{% if point.point_number %}: {% endif %}{{ point.point_type|title }}</h3>
            </div>
            
            <div class="point-content">
                <h4>Содержание документа:</h4>
                <p class="content-text">{{ point.point_content }}</p>
            </div>
            
            {% if point.analysis_points %}
            <div class="analysis-points">
                <h4>Правовой анализ:</h4>
                {% for analysis_point in point.analysis_points %}
                <div class="analysis-item">
                    <div class="problem-header">
                        <h5>Проблема {{ loop.index }}:</h5>
                    </div>
                    
                    <div class="analysis-section">
                        <h6>Выявленная проблема:</h6>
                        <p>{{ analysis_point.cause }}</p>
                    </div>
                    
                    <div class="analysis-section">
                        <h6>Оценка риска:</h6>
                        <p class="risk-text {% if 'высокий' in analysis_point.risk.lower() or 'high' in analysis_point.risk.lower() %}risk-high-text{% elif 'средний' in analysis_point.risk.lower() or 'medium' in analysis_point.risk.lower() %}risk-medium-text{% elif 'низкий' in analysis_point.risk.lower() or 'low' in analysis_point.risk.lower() %}risk-low-text{% endif %}">
                            {{ analysis_point.risk }}
                        </p>
                    </div>
                    
                    <div class="analysis-section">
                        <h6>Рекомендация:</h6>
                        <p>{{ analysis_point.recommendation }}</p>
                    </div>
                </div>
                {% if not loop.last %}<hr class="analysis-separator">{% endif %}
                {% endfor %}
            </div>
            {% else %}
            <div class="no-issues">
                <p>В данном разделе правовых проблем не выявлено.</p>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    <div class="footer">
        <p>Данный отчёт создан системой правового анализа SmartClause</p>
        <p>Дата создания: {{ generation_timestamp }}</p>
        <div class="disclaimer">
            <p><strong>Внимание:</strong> Данный отчёт не является юридическим заключением и носит исключительно информационный характер. Для получения профессиональной правовой помощи обратитесь к квалифицированному юристу.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return {
            'analysis_report': analysis_report_template
        }
    
    def _get_pdf_styles(self) -> str:
        """Get CSS styles for PDF generation"""
        
        return """
        @page {
            margin: 2cm;
            @top-center {
                content: "Отчёт о правовом анализе";
                font-family: Arial, sans-serif;
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Страница " counter(page) " из " counter(pages);
                font-family: Arial, sans-serif;
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #0c1a2e;
        }
        
        .header h1 {
            color: #0c1a2e;
            font-size: 24pt;
            margin: 0 0 10px 0;
            font-weight: bold;
        }
        
        .document-info h2 {
            color: #1e293b;
            font-size: 18pt;
            margin: 10px 0 5px 0;
        }
        
        .timestamp {
            color: #666;
            font-size: 10pt;
            margin: 2px 0;
        }
        
        .summary {
            background-color: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .summary h2 {
            color: #0c1a2e;
            font-size: 16pt;
            margin: 0 0 15px 0;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 15px;
        }
        
        .summary-item {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }
        
        .summary-item .number {
            display: block;
            font-size: 20pt;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .summary-item .label {
            font-size: 10pt;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .risk-high .number { color: #e53e3e; }
        .risk-medium .number { color: #dd6b20; }
        .risk-low .number { color: #38a169; }
        
        .analysis-details h2 {
            color: #0c1a2e;
            font-size: 16pt;
            margin: 20px 0 15px 0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .document-point {
            margin-bottom: 25px;
        }
        
        .point-header h3 {
            color: #1e293b;
            font-size: 14pt;
            margin: 0 0 15px 0;
            padding: 10px;
            background-color: #f1f5f9;
            border-left: 4px solid #0c1a2e;
        }
        
        .point-content {
            margin-bottom: 20px;
        }
        
        .point-content h4,
        .analysis-points h4 {
            color: #374151;
            font-size: 12pt;
            margin: 0 0 8px 0;
            font-weight: 600;
        }
        
        .content-text {
            background-color: #f9fafb;
            padding: 15px;
            border-left: 3px solid #d1d5db;
            margin: 0;
            font-style: italic;
        }
        
        .analysis-points {
            background-color: #fefefe;
            padding: 20px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
        }
        
        .analysis-item {
            margin-bottom: 25px;
            padding: 15px;
            background-color: #fbfbfb;
            border-radius: 6px;
            border-left: 3px solid #e5e7eb;
        }
        
        .problem-header h5 {
            color: #1f2937;
            font-size: 12pt;
            margin: 0 0 12px 0;
            font-weight: 700;
            padding: 8px 12px;
            background-color: #f3f4f6;
            border-radius: 4px;
            border-left: 3px solid #6b7280;
        }
        
        .analysis-section {
            margin-bottom: 12px;
            padding-left: 10px;
        }
        
        .analysis-section h6 {
            color: #4b5563;
            font-size: 10pt;
            margin: 0 0 5px 0;
            font-weight: 600;
        }
        
        .analysis-section p {
            margin: 0;
            padding-left: 10px;
        }
        
        .risk-high-text { color: #e53e3e; font-weight: bold; }
        .risk-medium-text { color: #dd6b20; font-weight: bold; }
        .risk-low-text { color: #38a169; font-weight: bold; }
        
        .analysis-separator {
            border: none;
            border-top: 2px solid #e5e7eb;
            margin: 20px 0;
        }
        
        .no-issues {
            background-color: #f0fdf4;
            padding: 15px;
            border: 1px solid #bbf7d0;
            border-radius: 6px;
            color: #166534;
        }
        
        .no-issues p {
            margin: 0;
            font-style: italic;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            color: #666;
            font-size: 9pt;
        }
        
        .footer p {
            margin: 3px 0;
        }
        
        .disclaimer {
            margin-top: 15px;
            padding: 10px 0;
            border-top: 1px solid #e2e8f0;
            text-align: left;
        }
        
        .disclaimer p {
            margin: 0;
            color: #666;
            font-size: 9pt;
            line-height: 1.4;
            font-style: italic;
        }
        
        .disclaimer strong {
            font-weight: 600;
            color: #555;
        }
        """


# Global instance
export_service = ExportService() 