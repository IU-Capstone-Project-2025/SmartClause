"""
Export Service for Analysis Results

Handles generation of PDF, CSV, and JSON exports from analysis data.
"""

import io
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import asyncio

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
    """
    Service for exporting analysis results in various formats
    
    Features:
    - PDF export with professional legal report formatting
    - LLM-generated executive summary/abstract of all analysis issues
    - Statistics and risk categorization
    - Detailed analysis breakdown by document points
    
    The PDF export includes:
    1. Executive Summary: LLM-generated abstract of key issues and risks
    2. Statistical Overview: Counts of points, issues, and risk levels
    3. Detailed Analysis: Point-by-point legal analysis with recommendations
    
    The LLM summary provides a concise 2-3 sentence overview that:
    - Summarizes the main types of legal issues found
    - Indicates overall risk level
    - Provides general recommendations for the document
    """
    
    def __init__(self):
        self.jinja_env = Environment(loader=DictLoader(self._get_templates()))
        self.font_config = FontConfiguration() if WEASYPRINT_AVAILABLE else None
        self._analyzer_service = None
    
    def _get_analyzer_service(self):
        """Lazy load analyzer service to access LLM client"""
        if self._analyzer_service is None:
            from .analyzer_service import analyzer_service
            self._analyzer_service = analyzer_service
        return self._analyzer_service

    async def _generate_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate a concise summary/abstract of all analysis issues using LLM
        
        Args:
            analysis_data: Analysis results dictionary
            
        Returns:
            str: Generated summary text
        """
        try:
            analyzer = self._get_analyzer_service()
            
            # Extract all issues from analysis data
            document_points = analysis_data.get('document_points', [])
            all_issues = []
            
            for point in document_points:
                for analysis_point in point.get('analysis_points', []):
                    all_issues.append({
                        'point_number': point.get('point_number', ''),
                        'point_type': point.get('point_type', ''),
                        'cause': analysis_point.get('cause', ''),
                        'risk': analysis_point.get('risk', ''),
                        'recommendation': analysis_point.get('recommendation', '')
                    })
            
            if not all_issues:
                return "В ходе анализа документа существенных правовых проблем или рисков не выявлено. Документ соответствует основным требованиям российского законодательства."
            
            # Create prompt for summary generation
            issues_text = ""
            for i, issue in enumerate(all_issues, 1):
                issues_text += f"{i}. Пункт {issue['point_number']} ({issue['point_type']}): {issue['cause']} - {issue['risk']}\n"
            
            prompt = f"""
Ты — старший юрист-аналитик. Твоя задача — создать краткое резюме (abstract) правового анализа документа.

НАЙДЕННЫЕ ПРОБЛЕМЫ И РИСКИ:
{issues_text}

ЗАДАЧА:
Создай краткое резюме (2-3 предложения) который:
1. Обобщает основные типы выявленных проблем
2. Указывает общий уровень правовых рисков
3. Дает общую рекомендацию по документу

ТРЕБОВАНИЯ:
- Максимум 150 слов
- Профессиональный юридический стиль
- Конкретные выводы без лишней детализации
- На русском языке

ФОРМАТ ОТВЕТА:
Простой текст без форматирования, markdown или JSON.

ПРИМЕР:
"Анализ выявил 5 существенных правовых проблем, включая неопределенные сроки исполнения и несбалансированные штрафные санкции. Общий уровень правовых рисков оценивается как средний с элементами высокого риска в области ответственности сторон. Рекомендуется доработка договора с уточнением ключевых условий и приведением спорных пунктов в соответствие с требованиями ГК РФ."
"""
            
            # Call LLM to generate summary
            summary = await analyzer._call_llm(prompt, temperature=0.3)
            
            # Clean and validate summary
            summary = summary.strip()
            if not summary or len(summary) < 20:
                return f"Анализ выявил {len(all_issues)} правовых проблем различного уровня сложности. Рекомендуется внимательное изучение каждого пункта и консультация с юристом для устранения выявленных недочетов."
            
            logger.info(f"Generated analysis summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate analysis summary: {e}")
            # Fallback summary
            document_points = analysis_data.get('document_points', [])
            total_issues = sum(len(point.get('analysis_points', [])) for point in document_points)
            
            if total_issues == 0:
                return "В ходе анализа документа существенных правовых проблем или рисков не выявлено."
            else:
                return f"Анализ выявил {total_issues} потенциальных правовых проблем. Рекомендуется детальное изучение каждого пункта и консультация с квалифицированным юристом."

    async def export_analysis_pdf(self, analysis_data: Dict[str, Any]) -> bytes:
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
            # Generate analysis summary using LLM
            logger.info("Generating analysis summary using LLM...")
            analysis_summary = await self._generate_analysis_summary(analysis_data)
            
            # Prepare template data
            template_data = self._prepare_template_data(analysis_data)
            template_data['analysis_summary'] = analysis_summary
            
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
    
    {% if analysis_summary %}
    <div class="executive-summary">
        <h2>Резюме анализа</h2>
        <p class="summary-text">{{ analysis_summary }}</p>
    </div>
    {% endif %}
    
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
        
        .executive-summary {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #0c1a2e;
        }
        
        .executive-summary h2 {
            color: #0c1a2e;
            font-size: 16pt;
            margin: 0 0 15px 0;
            font-weight: bold;
        }
        
        .summary-text {
            font-size: 12pt;
            line-height: 1.7;
            margin: 0;
            color: #1e293b;
            font-weight: 500;
            text-align: justify;
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

    async def export_analysis_as_pdf(self, document_id: str, db, user_id: str) -> bytes:
        """Retrieve analysis results for the given document ID from the database and export them as a PDF.

        Args:
            document_id: The ID of the document whose analysis should be exported.
            db: SQLAlchemy session for DB access.
            user_id: ID of the requesting user (can be "system" for service account). Used for access logging.

        Returns:
            PDF bytes generated from the analysis results.
        """
        import logging
        from sqlalchemy import desc
        from ..models.database import AnalysisResult

        logger = logging.getLogger(__name__)
        logger.info(f"ExportService.export_analysis_as_pdf called for document_id={document_id} by user={user_id}")

        # Fetch the most recent analysis result for the document.
        try:
            analysis_result: AnalysisResult = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.document_id == document_id)
                .order_by(desc(AnalysisResult.created_at))
                .first()
            )
        except Exception as e:
            logger.error(f"Database error when querying AnalysisResult: {e}")
            raise ValueError("Database error while retrieving analysis results")

        if not analysis_result:
            logger.warning(f"No analysis results found for document_id={document_id}")
            raise ValueError("Analysis results not found for the specified document")

        analysis_data = analysis_result.analysis_points  # Stored as JSON in DB

        if not analysis_data:
            logger.warning(f"Analysis data is empty for document_id={document_id}")
            raise ValueError("Analysis data is empty for the specified document")

        # Generate PDF using existing helper.
        pdf_bytes = await self.export_analysis_pdf(analysis_data)
        return pdf_bytes


# Global instance
export_service = ExportService() 