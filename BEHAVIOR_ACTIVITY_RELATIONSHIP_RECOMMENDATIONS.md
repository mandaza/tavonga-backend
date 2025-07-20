# Behavior-Activity Relationship Implementation Guide

## Overview
This document outlines the recommended implementation for adding relationships between behavior logs and activities in the Tavonga Support System backend API.

## Current State Analysis

### Existing Models
- **BehaviorLog**: Comprehensive behavior tracking with user, date, location, severity, intervention details
- **Activity**: Activity definitions with goal associations and categorization
- **ActivityLog**: Instance tracking of activity execution with completion status

### Missing Relationships
- No structured relationship between behaviors and activities
- Only text-based `activity_before` field in BehaviorLog
- No ability to track activity-triggered behaviors or behavior patterns during activities

## Recommended Implementation

### 1. Database Schema Changes

#### New Fields in BehaviorLog Model
```python
# Direct activity relationship
related_activity = models.ForeignKey(
    'activities.Activity', 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True,
    related_name='behavior_logs'
)

# Specific activity instance relationship
related_activity_log = models.ForeignKey(
    'activities.ActivityLog', 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True,
    related_name='behavior_logs'
)

# Timing context
behavior_occurrence = models.CharField(
    max_length=20, 
    choices=[
        ('before_activity', 'Before Activity'),
        ('during_activity', 'During Activity'),
        ('after_activity', 'After Activity'),
        ('unrelated', 'Unrelated to Activity')
    ],
    default='unrelated'
)
```

#### Relationship Types
1. **Activity-Level Relationship**: Links behavior to general activity type
2. **Activity Log Relationship**: Links behavior to specific activity execution instance
3. **Occurrence Timing**: When the behavior occurred relative to the activity

### 2. API Enhancements

#### New Endpoints
- `/api/behaviors/activity-related/` - Get activity-related behavior logs
- `/api/behaviors/activity-triggers/` - Get behaviors triggered by activities
- `/api/behaviors/activity-analytics/` - Comprehensive activity-behavior analytics
- `/api/behaviors/activity-recommendations/` - AI-driven recommendations

#### Enhanced Filtering
- Filter by `related_activity`
- Filter by `behavior_occurrence`
- Filter by `is_activity_related`

#### New Serializer Fields
- `related_activity` - Activity details
- `related_activity_log` - Activity log instance
- `behavior_occurrence` - Timing context
- `is_activity_related` - Boolean indicator
- `activity_context` - Comprehensive context information

### 3. Analytics & Insights

#### Activity Analytics Dashboard
```json
{
  "total_behaviors": 150,
  "activity_related_behaviors": 45,
  "activity_related_percentage": 30.0,
  "occurrence_statistics": [
    {"behavior_occurrence": "during_activity", "count": 20},
    {"behavior_occurrence": "after_activity", "count": 15},
    {"behavior_occurrence": "before_activity", "count": 10}
  ],
  "problematic_activities": [
    {
      "related_activity__id": 1,
      "related_activity__name": "Mathematics Session",
      "related_activity__category": "educational",
      "behavior_count": 12,
      "critical_count": 3
    }
  ]
}
```

#### Activity Risk Assessment
Each activity now includes:
- `behavior_incident_count` - Total behavior incidents
- `behavior_risk_level` - Risk assessment (low/medium/high)
- `critical_behavior_count` - Critical incidents
- `behavior_statistics` - Comprehensive statistics

### 4. Implementation Steps

#### Phase 1: Database Migration
1. Create migration file with new fields
2. Run migration: `python manage.py makemigrations behaviors`
3. Apply migration: `python manage.py migrate`

#### Phase 2: Model Updates
1. Update BehaviorLog model with new fields and properties
2. Update Activity model with behavior-related properties
3. Test model relationships

#### Phase 3: API Updates
1. Update serializers to include new fields
2. Add validation logic for activity relationships
3. Update viewsets with new filtering options
4. Add new analytics endpoints

#### Phase 4: Frontend Integration
1. Update mobile app models to include new fields
2. Modify behavior logging forms to include activity selection
3. Add activity-behavior analytics screens
4. Update web dashboard with new insights

### 5. Usage Examples

#### Creating a Behavior Log with Activity Context
```python
# During an activity
behavior_log = BehaviorLog.objects.create(
    user=user,
    date=datetime.now().date(),
    time=datetime.now().time(),
    related_activity=activity,
    related_activity_log=activity_log,
    behavior_occurrence='during_activity',
    behavior_type='non_compliance',
    severity='medium',
    intervention_used='Redirection to preferred activity'
)
```

#### Querying Activity-Behavior Relationships
```python
# Get all behaviors during math activities
math_behaviors = BehaviorLog.objects.filter(
    related_activity__category='educational',
    related_activity__name__icontains='math',
    behavior_occurrence='during_activity'
)

# Get high-risk activities
high_risk_activities = Activity.objects.filter(
    behavior_logs__severity='critical'
).distinct()
```

### 6. Benefits

#### For Carers
- Better understanding of behavior triggers
- Improved activity planning based on behavior patterns
- More targeted interventions

#### For Administrators
- Data-driven activity modifications
- Risk assessment for activities
- Evidence-based program improvements

#### For Data Analysis
- Correlation analysis between activities and behaviors
- Predictive modeling for behavior incidents
- Intervention effectiveness tracking

### 7. Advanced Features (Future Enhancements)

#### Predictive Analytics
- ML models to predict behavior incidents during specific activities
- Risk scoring for activity-user combinations
- Proactive intervention recommendations

#### Automated Insights
- Real-time alerts for high-risk activity patterns
- Automatic behavior pattern recognition
- Intervention effectiveness scoring

#### Integration with Goals
- Link behavior patterns to goal achievement
- Activity recommendation engine based on behavior history
- Progress tracking with behavior context

### 8. Data Privacy & Security

#### Considerations
- Ensure behavior-activity relationships don't compromise user privacy
- Implement proper access controls for sensitive analytics
- Maintain audit trails for behavior-activity associations

#### Compliance
- Follow existing data protection protocols
- Ensure proper consent for behavior tracking
- Implement data retention policies

### 9. Testing Strategy

#### Unit Tests
- Model relationship validation
- Serializer field validation
- Analytics calculation accuracy

#### Integration Tests
- API endpoint functionality
- Cross-app model relationships
- Data consistency checks

#### Performance Tests
- Analytics query performance
- Large dataset handling
- Real-time insight generation

### 10. Migration Considerations

#### Backward Compatibility
- Existing `activity_before` field maintained
- Gradual migration of existing data
- API version compatibility

#### Data Migration
- Optional: Parse existing `activity_before` text to create structured relationships
- Bulk update scripts for historical data
- Validation of migrated data

This implementation provides a comprehensive solution for tracking behavior-activity relationships while maintaining system integrity and performance. 