from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from behaviors.models import BehaviorLog
from users.models import User
import csv
from datetime import datetime
from activities.models import ActivityLog
from shifts.models import Shift
from goals.models import Goal
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from io import BytesIO

# Create your views here.

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and getattr(request.user, 'is_admin', False)

class BehaviorLogReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Filters
        start = request.GET.get('start')
        end = request.GET.get('end')
        severity = request.GET.get('severity')
        user_id = request.GET.get('user')
        export_format = request.GET.get('format', 'csv')

        logs = BehaviorLog.objects.all()
        if start:
            logs = logs.filter(date__gte=start)
        if end:
            logs = logs.filter(date__lte=end)
        if severity:
            logs = logs.filter(severity=severity)
        if user_id:
            logs = logs.filter(user_id=user_id)

        if export_format == 'csv':
            # CSV export
            response = HttpResponse(content_type='text/csv')
            filename = f"behavior_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'User', 'Date', 'Time', 'Location', 'Type', 'Severity',
                'Behaviors', 'Harm to Self', 'Harm to Others', 'Intervention', 'Notes'
            ])
            for log in logs:
                writer.writerow([
                    log.id,
                    log.user.get_full_name() or log.user.username,
                    log.date,
                    log.time,
                    log.location,
                    log.behavior_type,
                    log.severity,
                    ", ".join(log.behaviors) if isinstance(log.behaviors, list) else log.behaviors,
                    log.harm_to_self,
                    log.harm_to_others,
                    log.intervention_used,
                    log.notes,
                ])
            return response
        elif export_format == 'pdf':
            rows = [
                ['ID', 'User', 'Date', 'Time', 'Location', 'Type', 'Severity',
                 'Behaviors', 'Harm to Self', 'Harm to Others', 'Intervention', 'Notes']
            ]
            for log in logs:
                rows.append([
                    log.id,
                    log.user.get_full_name() or log.user.username,
                    log.date,
                    log.time,
                    log.location,
                    log.behavior_type,
                    log.severity,
                    ", ".join(log.behaviors) if isinstance(log.behaviors, list) else log.behaviors,
                    log.harm_to_self,
                    log.harm_to_others,
                    log.intervention_used,
                    log.notes,
                ])
            buffer = render_pdf_table(rows[0], rows[1:], 'Behavior Logs Report')
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="behavior_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            return response
        else:
            # JSON fallback
            data = [
                {
                    'id': log.id,
                    'user': log.user.get_full_name() or log.user.username,
                    'date': log.date,
                    'time': log.time,
                    'location': log.location,
                    'type': log.behavior_type,
                    'severity': log.severity,
                    'behaviors': log.behaviors,
                    'harm_to_self': log.harm_to_self,
                    'harm_to_others': log.harm_to_others,
                    'intervention': log.intervention_used,
                    'notes': log.notes,
                }
                for log in logs
            ]
            return Response(data)

def render_pdf_table(header, rows, title):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 40, title)
    data = [header] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(c, width, height)
    table_height = 30 * (len(data))
    table.drawOn(c, 30, height - 70 - table_height)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

class ActivityLogReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        user_id = request.GET.get('user')
        status = request.GET.get('status')
        export_format = request.GET.get('format', 'csv')

        logs = ActivityLog.objects.all()
        if start:
            logs = logs.filter(date__gte=start)
        if end:
            logs = logs.filter(date__lte=end)
        if user_id:
            logs = logs.filter(user_id=user_id)
        if status:
            logs = logs.filter(status=status)

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"activity_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'User', 'Activity', 'Date', 'Status', 'Completed', 'Notes', 'Challenges', 'Successes'
            ])
            for log in logs:
                writer.writerow([
                    log.id,
                    log.user.get_full_name() or log.user.username,
                    log.activity.name if log.activity else '',
                    log.date,
                    log.status,
                    log.completed,
                    log.notes,
                    log.challenges,
                    log.successes,
                ])
            return response
        elif export_format == 'pdf':
            rows = [
                ['ID', 'User', 'Activity', 'Date', 'Status', 'Completed', 'Notes', 'Challenges', 'Successes']
            ]
            for log in logs:
                rows.append([
                    log.id,
                    log.user.get_full_name() or log.user.username,
                    log.activity.name if log.activity else '',
                    log.date,
                    log.status,
                    log.completed,
                    log.notes,
                    log.challenges,
                    log.successes,
                ])
            buffer = render_pdf_table(rows[0], rows[1:], 'Activity Logs Report')
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            return response
        else:
            data = [
                {
                    'id': log.id,
                    'user': log.user.get_full_name() or log.user.username,
                    'activity': log.activity.name if log.activity else '',
                    'date': log.date,
                    'status': log.status,
                    'completed': log.completed,
                    'notes': log.notes,
                    'challenges': log.challenges,
                    'successes': log.successes,
                }
                for log in logs
            ]
            return Response(data)

class ShiftReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        carer_id = request.GET.get('carer')
        status = request.GET.get('status')
        export_format = request.GET.get('format', 'csv')

        shifts = Shift.objects.all()
        if start:
            shifts = shifts.filter(date__gte=start)
        if end:
            shifts = shifts.filter(date__lte=end)
        if carer_id:
            shifts = shifts.filter(carer_id=carer_id)
        if status:
            shifts = shifts.filter(status=status)

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"shifts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Carer', 'Date', 'Shift Type', 'Start Time', 'End Time', 'Status', 'Clock In', 'Clock Out', 'Location', 'Notes'
            ])
            for shift in shifts:
                writer.writerow([
                    shift.id,
                    shift.carer.get_full_name() or shift.carer.username,
                    shift.date,
                    shift.shift_type,
                    shift.start_time,
                    shift.end_time,
                    shift.status,
                    shift.clock_in,
                    shift.clock_out,
                    shift.location,
                    shift.notes,
                ])
            return response
        elif export_format == 'pdf':
            rows = [
                ['ID', 'Carer', 'Date', 'Shift Type', 'Start Time', 'End Time', 'Status', 'Clock In', 'Clock Out', 'Location', 'Notes']
            ]
            for shift in shifts:
                rows.append([
                    shift.id,
                    shift.carer.get_full_name() or shift.carer.username,
                    shift.date,
                    shift.shift_type,
                    shift.start_time,
                    shift.end_time,
                    shift.status,
                    shift.clock_in,
                    shift.clock_out,
                    shift.location,
                    shift.notes,
                ])
            buffer = render_pdf_table(rows[0], rows[1:], 'Shifts Report')
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="shifts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            return response
        else:
            data = [
                {
                    'id': shift.id,
                    'carer': shift.carer.get_full_name() or shift.carer.username,
                    'date': shift.date,
                    'shift_type': shift.shift_type,
                    'start_time': shift.start_time,
                    'end_time': shift.end_time,
                    'status': shift.status,
                    'clock_in': shift.clock_in,
                    'clock_out': shift.clock_out,
                    'location': shift.location,
                    'notes': shift.notes,
                }
                for shift in shifts
            ]
            return Response(data)

class GoalProgressReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        created_by = request.GET.get('created_by')
        status = request.GET.get('status')
        export_format = request.GET.get('format', 'csv')

        goals = Goal.objects.all()
        if start:
            goals = goals.filter(created_at__gte=start)
        if end:
            goals = goals.filter(created_at__lte=end)
        if created_by:
            goals = goals.filter(created_by_id=created_by)
        if status:
            goals = goals.filter(status=status)

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"goals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Name', 'Description', 'Category', 'Status', 'Priority', 'Target Date',
                'Progress (%)', 'Created By', 'Assigned Carers', 'Created At', 'Updated At', 'Notes'
            ])
            for goal in goals:
                writer.writerow([
                    goal.id,
                    goal.name,
                    goal.description,
                    goal.category,
                    goal.status,
                    goal.priority,
                    goal.target_date,
                    goal.progress_percentage,
                    goal.created_by.get_full_name() if goal.created_by else '',
                    ", ".join([c.get_full_name() or c.username for c in goal.assigned_carers.all()]),
                    goal.created_at,
                    goal.updated_at,
                    goal.notes,
                ])
            return response
        elif export_format == 'pdf':
            rows = [
                ['ID', 'Name', 'Description', 'Category', 'Status', 'Priority', 'Target Date',
                 'Progress (%)', 'Created By', 'Assigned Carers', 'Created At', 'Updated At', 'Notes']
            ]
            for goal in goals:
                rows.append([
                    goal.id,
                    goal.name,
                    goal.description,
                    goal.category,
                    goal.status,
                    goal.priority,
                    goal.target_date,
                    goal.progress_percentage,
                    goal.created_by.get_full_name() if goal.created_by else '',
                    ", ".join([c.get_full_name() or c.username for c in goal.assigned_carers.all()]),
                    goal.created_at,
                    goal.updated_at,
                    goal.notes,
                ])
            buffer = render_pdf_table(rows[0], rows[1:], 'Goals Report')
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="goals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            return response
        else:
            data = [
                {
                    'id': goal.id,
                    'name': goal.name,
                    'description': goal.description,
                    'category': goal.category,
                    'status': goal.status,
                    'priority': goal.priority,
                    'target_date': goal.target_date,
                    'progress_percentage': goal.progress_percentage,
                    'created_by': goal.created_by.get_full_name() if goal.created_by else '',
                    'assigned_carers': [c.get_full_name() or c.username for c in goal.assigned_carers.all()],
                    'created_at': goal.created_at,
                    'updated_at': goal.updated_at,
                    'notes': goal.notes,
                }
                for goal in goals
            ]
            return Response(data)
