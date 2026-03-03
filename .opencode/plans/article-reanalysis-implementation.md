# Article Reanalysis Feature Implementation Plan

## User Requirements
1. Show "analyzing again" indicator when reanalysis is triggered
2. Preserve and display previous sentiment data during reanalysis
3. Notify user when reanalysis completes
4. Support bulk reanalysis from news list
5. Use polling approach for status tracking

## Implementation Overview

### Backend Changes

#### 1. Create `app/services/reanalysis_status.py`
Redis-based status tracking service for individual article reanalysis.

**Key Components:**
- `ReanalysisStatus` enum: PENDING, STARTED, ANALYZING, COMPLETED, FAILED
- `ReanalysisStatusService` class with methods:
  - `start_reanalysis(article_id, task_id, user_id)` - Initialize tracking
  - `update_progress(article_id, progress)` - Update progress during analysis
  - `complete_reanalysis(article_id, result)` - Mark as completed
  - `fail_reanalysis(article_id, error)` - Mark as failed
  - `get_status(article_id)` - Get current status
  - `is_reanalyzing(article_id)` - Check if active

**Redis Schema:**
- Key: `reanalysis:article:{article_id}`
- TTL: 300s (5 min) during analysis, 60s after completion
- Value: JSON with status, timestamps, progress, result/error

#### 2. Modify `app/api/v1/sentiment.py`

**New Endpoint:**
```python
GET /sentiment/reanalyze/article/{article_id}/status
Response: {
    "article_id": str,
    "status": "started|analyzing|completed|failed",
    "task_id": str,
    "started_at": str | None,
    "completed_at": str | None,
    "progress": dict | None,
    "result": dict | None,
    "error": str | None
}
```

**Modified Endpoint:**
```python
POST /sentiment/reanalyze
- Store task mappings in Redis via ReanalysisStatusService
- Return same response shape plus tracking capability
```

#### 3. Modify `pipeline/pipeline/tasks/sentiment_analysis.py`

**In `analyze_article` task:**
- On task start: Call `start_reanalysis()` via Redis
- During analysis (if possible): Call `update_progress()`
- On success: Call `complete_reanalysis()` with result
- On failure: Call `fail_reanalysis()` with error

### Frontend Changes

#### 1. Modify `frontend/src/lib/api.ts`

**New Types:**
```typescript
interface ArticleReanalysisStatus {
  article_id: string;
  status: "pending" | "started" | "analyzing" | "completed" | "failed";
  task_id: string;
  started_at: string | null;
  completed_at: string | null;
  progress: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
}
```

**New Functions:**
```typescript
getArticleReanalysisStatus(articleId: string): Promise<ArticleReanalysisStatus | null>
```

#### 2. Create `frontend/src/components/news/reanalyzing-badge.tsx`

**Component:** Animated badge showing reanalysis status
- Pulsing dot animation using Tailwind `animate-pulse`
- Text: "Analyzing again..." with optional progress
- Styled as a small badge/badge variant
- Props: `status`, `progress`, `className`

#### 3. Modify `frontend/src/components/news/news-detail.tsx`

**State Additions:**
```typescript
const [reanalysisTaskId, setReanalysisTaskId] = useState<string | null>(null);
```

**Polling Logic:**
```typescript
const { data: reanalysisStatus } = useQuery({
  queryKey: ["reanalysis-status", id],
  queryFn: () => getArticleReanalysisStatus(id),
  enabled: !!reanalysisTaskId,
  refetchInterval: (query) => {
    const data = query.state.data;
    if (!data || ["completed", "failed"].includes(data.status)) {
      return false;
    }
    return 2000; // Poll every 2 seconds
  },
});
```

**UI Changes:**
- Reanalyze button shows loading spinner when `reanalyzeMutation.isPending`
- When `reanalysisStatus?.status` is active, show `ReanalyzingBadge` next to sentiment score
- Previous sentiment data remains visible
- On completion: Show Sonner toast "Reanalysis complete!" and invalidate article query
- On failure: Show Sonner toast with error message

#### 4. Modify `frontend/src/components/news/news-card.tsx`

**Additions:**
- Checkbox for bulk selection (visible in list view)
- Small reanalysis status indicator (dot/spinner)
- Reanalyze button with loading state

**Props:**
```typescript
interface NewsCardProps {
  article: NewsArticleListItem;
  selectable?: boolean;
  selected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  showReanalyze?: boolean;
}
```

#### 5. Modify `frontend/src/app/news/page.tsx`

**State Additions:**
```typescript
const [selectedArticles, setSelectedArticles] = useState<Set<string>>(new Set());
const [isBulkReanalyzing, setIsBulkReanalyzing] = useState(false);
```

**UI Additions:**
- Toolbar with:
  - "Select All" / "Deselect All" buttons
  - "Reanalyze Selected (N)" button (disabled when none selected)
  - Bulk reanalysis progress indicator
- Pass `selectable={true}` to NewsCard components

**Bulk Reanalysis Logic:**
- Call `reanalyzeSentiment(Array.from(selectedArticles))`
- Track task IDs returned
- Show progress toast with count
- Poll for each article's completion
- Show completion toast when all done

## File Changes Summary

### Backend
1. **NEW** `backend/app/services/reanalysis_status.py` - Status tracking service
2. **MODIFY** `backend/app/api/v1/sentiment.py` - Add status endpoint, integrate service
3. **MODIFY** `backend/pipeline/pipeline/tasks/sentiment_analysis.py` - Update task to report progress

### Frontend
1. **MODIFY** `frontend/src/lib/api.ts` - Add status API function and types
2. **NEW** `frontend/src/components/news/reanalyzing-badge.tsx` - Animated status badge
3. **MODIFY** `frontend/src/components/news/news-detail.tsx` - Add polling and UI state
4. **MODIFY** `frontend/src/components/news/news-card.tsx` - Add selection and status
5. **MODIFY** `frontend/src/app/news/page.tsx` - Add bulk reanalysis toolbar

## Technical Decisions

1. **Polling over WebSocket**: Simpler implementation, easier to debug, sufficient for this use case
2. **Redis TTL**: 5 minutes during analysis prevents stale data buildup
3. **Status Persistence**: Keep status for 1 minute after completion to allow frontend to detect completion
4. **UI Pattern**: Badge with microanimation provides clear feedback without blocking content
5. **Bulk Reanalysis**: Leverage existing `/sentiment/reanalyze` endpoint which already supports multiple articles

## Testing Strategy

1. **Unit Tests**: Test ReanalysisStatusService methods
2. **Integration Tests**: Test API endpoint with mocked Redis
3. **E2E Tests**: Manual testing flow:
   - Click reanalyze on article detail
   - Verify badge appears
   - Verify previous data visible
   - Wait for completion toast
   - Verify data refreshes
   - Test bulk reanalysis from list

## Future Enhancements (Not in Scope)

1. WebSocket real-time updates for lower latency
2. Reanalysis history tracking in database
3. Reanalysis queue with priority
4. Progress percentage (currently binary: started/completed)
