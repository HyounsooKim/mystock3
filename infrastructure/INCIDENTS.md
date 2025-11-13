# MyStock3 Incident Response Guide

## Overview

This document provides procedures for responding to production incidents affecting MyStock3 application availability, performance, or security.

**Last Updated**: 2025-11-13  
**Version**: 1.0.0  
**Maintained by**: DevOps & Engineering Team

---

## Table of Contents

1. [Incident Severity Levels](#incident-severity-levels)
2. [Incident Response Process](#incident-response-process)
3. [Common Incidents](#common-incidents)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Communication Templates](#communication-templates)
6. [Post-Incident Review](#post-incident-review)

---

## Incident Severity Levels

### SEV-1: Critical (P0)

**Impact**: Complete service outage, data loss, security breach

**Response Time**: Immediate (15 minutes)

**Examples**:
- Application completely down (health check failing)
- Database unavailable or data corruption
- Security breach or data leak
- Payment system failures

**Actions**:
- Page on-call engineer immediately
- Create war room (Teams/Slack)
- Executive notification within 30 minutes
- Customer communication within 1 hour

### SEV-2: High (P1)

**Impact**: Major feature unavailable, severe performance degradation

**Response Time**: 1 hour

**Examples**:
- Authentication system down
- Portfolio or watchlist features broken
- API latency >2 seconds (p95)
- Alpha Vantage API integration failing

**Actions**:
- Alert on-call engineer
- Team lead notified within 30 minutes
- Status page update within 2 hours

### SEV-3: Medium (P2)

**Impact**: Minor feature degradation, affects some users

**Response Time**: 4 hours (business hours)

**Examples**:
- Dark mode not persisting
- Stock quote delays (but still working)
- Minor UI issues
- Non-critical monitoring gaps

**Actions**:
- Create ticket and assign to team
- Resolve within 1 business day

### SEV-4: Low (P3)

**Impact**: Cosmetic issues, nice-to-have improvements

**Response Time**: 1 week

**Examples**:
- UI polish requests
- Documentation updates
- Feature requests

**Actions**:
- Add to backlog for next sprint

---

## Incident Response Process

### Phase 1: Detection & Triage (0-15 minutes)

1. **Receive Alert**
   - PagerDuty notification
   - Monitoring dashboard alarm
   - User reports

2. **Acknowledge Incident**
   ```powershell
   # Log into incident management system
   # Acknowledge alert in PagerDuty
   # Join incident channel (#incident-YYYY-MM-DD-NNN)
   ```

3. **Initial Assessment**
   - Check health endpoint: `https://api.mystock3.example.com/health`
   - Review Application Insights dashboard
   - Check recent deployments
   - Determine severity level

4. **Declare Incident**
   ```markdown
   **Incident**: #INC-2025-11-13-001
   **Severity**: SEV-2
   **Status**: Investigating
   **Impact**: Authentication system returning 500 errors
   **Commander**: @engineer-name
   **Started**: 2025-11-13 14:30 UTC
   ```

### Phase 2: Investigation (15-60 minutes)

1. **Gather Data**
   ```powershell
   # Check Application Insights
   az monitor app-insights query `
     --app mystock3-prod `
     --analytics-query "exceptions | where timestamp > ago(1h) | summarize count() by type"
   
   # Check recent deployments
   az webapp deployment list `
     --resource-group rg-mystock3-prod `
     --name mystock3-backend-prod
   
   # Review logs
   az webapp log tail `
     --resource-group rg-mystock3-prod `
     --name mystock3-backend-prod
   ```

2. **Form Hypothesis**
   - Recent code changes?
   - Infrastructure changes?
   - External dependency failures?
   - Traffic spike or DDoS?

3. **Test Hypothesis**
   - Reproduce issue in staging
   - Check monitoring graphs
   - Review error patterns

### Phase 3: Mitigation (60-120 minutes)

1. **Quick Fixes (if possible)**
   - Restart affected services
   - Clear cache
   - Scale up resources
   - Enable fallback features

2. **Rollback (if needed)**
   ```powershell
   # Rollback backend deployment
   az webapp deployment slot swap `
     --resource-group rg-mystock3-prod `
     --name mystock3-backend-prod `
     --slot production `
     --target-slot previous
   
   # Verify health
   Invoke-WebRequest -Uri "https://api.mystock3.example.com/health"
   ```

3. **Validate Fix**
   - Check error rates
   - Monitor latency
   - Verify user reports
   - Run smoke tests

### Phase 4: Resolution & Communication

1. **Confirm Resolution**
   - All monitoring green
   - User reports resolved
   - Performance metrics normal

2. **Update Status**
   ```markdown
   **Incident Update**: #INC-2025-11-13-001
   **Status**: Resolved
   **Resolution**: Rolled back deployment to v1.2.3
   **Duration**: 1h 45m
   **Root Cause**: Database connection pool exhaustion
   **Next Steps**: Post-incident review scheduled for 2025-11-14
   ```

3. **Customer Communication**
   - Status page update
   - Email to affected users (if applicable)
   - Thank you message

---

## Common Incidents

### 1. Application Completely Down

**Symptoms**:
- Health check returning 500/503
- All API endpoints failing
- Frontend showing error page

**Diagnosis**:
```powershell
# Check App Service status
az webapp show --resource-group rg-mystock3-prod --name mystock3-backend-prod --query "state"

# Check recent logs
az webapp log tail --resource-group rg-mystock3-prod --name mystock3-backend-prod

# Check Cosmos DB
az cosmosdb show --resource-group rg-mystock3-prod --name mystock3-cosmos-prod --query "provisioningState"
```

**Mitigation**:
1. Restart App Service
2. Check environment variables
3. Verify Cosmos DB connection
4. Rollback if recent deployment
5. Scale up if resource exhaustion

### 2. Database Performance Issues

**Symptoms**:
- Slow API responses (>2s)
- High RU consumption
- Throttling errors (429)

**Diagnosis**:
```powershell
# Check RU consumption
az monitor metrics list `
  --resource <cosmos-resource-id> `
  --metric "TotalRequestUnits" `
  --start-time "2025-11-13T10:00:00Z"

# Check for throttling
az monitor app-insights query `
  --app mystock3-prod `
  --analytics-query "dependencies | where name == 'CosmosDB' | where resultCode == 429"
```

**Mitigation**:
1. Review inefficient queries
2. Check missing indexes (see INDEXING_STRATEGY.md)
3. Scale up RU/s if needed
4. Enable caching for hot data

### 3. Alpha Vantage API Failures

**Symptoms**:
- Stock quotes not loading
- "API rate limit exceeded" errors
- Stale data displayed

**Diagnosis**:
```powershell
# Check API call metrics
az monitor app-insights query `
  --app mystock3-prod `
  --analytics-query "dependencies | where name == 'AlphaVantageAPI' | summarize count() by resultCode"

# Check cache hit rate
az monitor app-insights query `
  --app mystock3-prod `
  --analytics-query "customMetrics | where name contains 'CacheHit' | summarize sum(value)"
```

**Mitigation**:
1. Verify API key validity
2. Check Alpha Vantage service status
3. Increase cache TTL temporarily
4. Enable degraded mode (show last cached data)
5. Switch to backup data provider (if available)

### 4. Authentication Issues

**Symptoms**:
- Login failures
- JWT token validation errors
- "Unauthorized" errors for valid users

**Diagnosis**:
```powershell
# Check auth errors
az monitor app-insights query `
  --app mystock3-prod `
  --analytics-query "requests | where name contains 'auth' | where success == false"

# Verify JWT secret
az keyvault secret show --vault-name mystock3-kv-prod --name jwt-secret-key
```

**Mitigation**:
1. Verify JWT secret hasn't changed
2. Check token expiration (7 days)
3. Review recent auth code changes
4. Check Key Vault access permissions

### 5. Memory Leak or Resource Exhaustion

**Symptoms**:
- App Service restarting frequently
- Increasing response times over time
- Out of memory errors

**Diagnosis**:
```powershell
# Check App Service metrics
az monitor metrics list `
  --resource <app-service-resource-id> `
  --metric "MemoryPercentage" "CpuPercentage"

# Check for memory leaks in code
# Review Application Insights memory usage trends
```

**Mitigation**:
1. Restart App Service for immediate relief
2. Scale up App Service Plan
3. Review code for memory leaks
4. Check for unbounded cache growth
5. Deploy hotfix if leak identified

### 6. DDoS Attack or Traffic Spike

**Symptoms**:
- Extremely high request volume
- Rate limiting triggered extensively
- Legitimate users affected

**Diagnosis**:
```powershell
# Check request rates
az monitor app-insights query `
  --app mystock3-prod `
  --analytics-query "requests | summarize count() by bin(timestamp, 1m) | order by timestamp desc"

# Identify source IPs
az monitor app-insights query `
  --app mystock3-prod `
  --analytics-query "requests | extend clientIP = tostring(customDimensions.client_ip) | summarize count() by clientIP | top 10 by count_"
```

**Mitigation**:
1. Enable Azure DDoS Protection
2. Block abusive IP addresses
3. Increase rate limits temporarily (if legitimate)
4. Enable CDN caching
5. Contact Azure support for DDoS mitigation

---

## Monitoring & Alerts

### Application Insights Queries

See `infrastructure/monitoring/queries.kql` for full list.

**Key Queries**:
- Error rate: `requests | where success == false`
- High latency: `requests | where duration > 1000`
- Alpha Vantage failures: `dependencies | where name == 'AlphaVantageAPI' | where success == false`
- Cache hit rate: `customMetrics | where name contains 'CacheHit'`

### Alert Configuration

```powershell
# Create alert for high error rate
az monitor metrics alert create `
  --name "HighErrorRate" `
  --resource-group rg-mystock3-prod `
  --scopes <app-insights-resource-id> `
  --condition "avg requests/failed > 10" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action <action-group-id>

# Create alert for high latency
az monitor metrics alert create `
  --name "HighLatency" `
  --resource-group rg-mystock3-prod `
  --scopes <app-insights-resource-id> `
  --condition "avg requests/duration > 2000" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action <action-group-id>
```

### Dashboard Links

- **Production Dashboard**: https://portal.azure.com/#dashboard/mystock3-prod
- **Application Insights**: https://portal.azure.com/#blade/AppInsights
- **Status Page**: https://status.mystock3.example.com

---

## Communication Templates

### Internal Notification (Slack/Teams)

```markdown
🚨 **INCIDENT ALERT** 🚨

**Incident ID**: #INC-2025-11-13-001
**Severity**: SEV-2
**Impact**: Authentication system returning 500 errors, ~20% of login attempts failing
**Status**: Investigating
**Commander**: @alice
**War Room**: #incident-2025-11-13-001
**Started**: 2025-11-13 14:30 UTC

**Timeline**:
- 14:30 - Alert triggered (error rate spike)
- 14:32 - Incident declared, Alice assigned as commander
- 14:35 - Initial investigation: recent deployment suspected
- 14:40 - Rollback initiated

**Next Update**: In 30 minutes or when status changes
```

### Customer Communication (Status Page)

```markdown
**Service Disruption - Authentication Issues**

**Status**: Investigating
**Impact**: Some users may experience difficulty logging in
**Started**: November 13, 2025 at 2:30 PM UTC

We are currently investigating issues with our authentication system. Some users may be unable to log in during this time. Our team is actively working to resolve this issue.

We will provide updates every 30 minutes until resolved.

**Last Updated**: November 13, 2025 at 2:45 PM UTC
```

### Resolution Notification

```markdown
**[RESOLVED] Authentication Issues**

**Status**: Resolved
**Duration**: 1 hour 45 minutes
**Impact**: Authentication system temporary unavailable

**Summary**:
Between 2:30 PM and 4:15 PM UTC, some users experienced login failures. This was caused by a database connection pool exhaustion issue introduced in our latest deployment. We rolled back to the previous version and all services are now operating normally.

**Actions Taken**:
- Rolled back deployment to v1.2.3
- Increased database connection pool size
- Added monitoring for connection pool metrics

**Prevention**:
- Added load testing for connection pool scenarios
- Improved pre-deployment validation

We apologize for any inconvenience this may have caused.

**Last Updated**: November 13, 2025 at 4:20 PM UTC
```

---

## Post-Incident Review

### Timeline Template

```markdown
# Post-Incident Review: #INC-2025-11-13-001

**Date**: 2025-11-13
**Duration**: 1h 45m
**Severity**: SEV-2
**Commander**: Alice Johnson

## Timeline

| Time (UTC) | Event |
|------------|-------|
| 14:30 | Alert triggered: High error rate on /auth/login |
| 14:32 | Incident declared (SEV-2) |
| 14:35 | Investigation started, recent deployment suspected |
| 14:40 | Rollback initiated to v1.2.3 |
| 14:50 | Rollback completed |
| 14:55 | Error rate normalized |
| 15:00 | Monitoring confirmed resolution |
| 15:15 | Incident closed |

## Root Cause

Database connection pool exhaustion due to unclosed connections in new user registration flow introduced in v1.3.0.

## Impact

- 1,247 failed login attempts (~20% of total)
- 87 users affected
- No data loss

## What Went Well

- Fast detection (2 minutes)
- Clear rollback procedure
- Good communication

## What Went Wrong

- Insufficient load testing
- Connection pool metrics not monitored
- No canary deployment

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Fix connection leak in registration code | Bob | 2025-11-14 | Open |
| Add connection pool monitoring | Alice | 2025-11-15 | Open |
| Implement canary deployments | DevOps | 2025-11-20 | Open |
| Update load testing scenarios | QA | 2025-11-16 | Open |
| Document connection pool best practices | Bob | 2025-11-17 | Open |

## Lessons Learned

1. Always test connection pool limits under load
2. Monitor all critical resources (CPU, memory, connections, RU)
3. Canary deployments can catch issues before full rollout
4. Rollback procedures worked well, keep them updated
```

---

## Emergency Contacts

| Role | Name | Phone | Email | Backup |
|------|------|-------|-------|--------|
| Engineering Lead | Alice Johnson | +1-555-0101 | alice@mystock3.com | Bob Smith |
| DevOps Lead | Bob Smith | +1-555-0102 | bob@mystock3.com | Carol White |
| Product Manager | Carol White | +1-555-0103 | carol@mystock3.com | Alice Johnson |
| Executive | Dave Brown | +1-555-0104 | dave@mystock3.com | - |

**PagerDuty**: https://mystock3.pagerduty.com  
**War Room**: Teams channel #incidents  
**Status Page**: https://status.mystock3.example.com

---

## Related Documentation

- [Deployment Runbook](./RUNBOOK.md)
- [Architecture Documentation](../README.md)
- [Monitoring Queries](./monitoring/queries.kql)
- [API Documentation](../specs/001-stock-portfolio-app/contracts/openapi.yaml)

---

**End of Incident Response Guide**
