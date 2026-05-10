# ApplyMap Deployment Guide

## GitHub Repository

✅ **Repository:** https://github.com/Galym7707/ApplyMap

**Latest commits:**
- Add comprehensive MIT Solve 2026 documentation
- Update README with detailed feature documentation
- Clean up artifacts and prepare for submission

---

## Hugging Face Deployment

### Step 1: Create Hugging Face Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Fill in details:
   - **Name:** `applymap`
   - **License:** MIT
   - **SDK:** Docker
   - **Hardware:** CPU Basic (free tier)

### Step 2: Connect GitHub Repository

**Option A: Direct Git Push**

```bash
# Add Hugging Face as remote
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/applymap

# Push to Hugging Face
git push huggingface main
```

**Option B: GitHub Integration**

1. In Space settings, go to "Files and versions"
2. Click "Connect to GitHub"
3. Select repository: `Galym7707/ApplyMap`
4. Enable auto-sync

### Step 3: Configure Environment Variables

In Space settings → "Settings" → "Repository secrets":

```bash
# Required
DATABASE_URL=postgresql://user:password@host:5432/applymap
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key

# Optional
GOOGLE_SEARCH_API_KEY=your-google-api-key
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id
```

### Step 4: Verify Deployment

1. Wait for build to complete (~5-10 minutes)
2. Check logs for errors
3. Visit Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/applymap`
4. Test basic functionality:
   - Sign up
   - Add achievement
   - Generate report

---

## Production Deployment (AWS/GCP)

### Prerequisites

- AWS/GCP account
- Domain name (optional)
- SSL certificate

### Backend Deployment

**Using Docker Compose:**

```bash
# Clone repository
git clone https://github.com/Galym7707/ApplyMap.git
cd ApplyMap

# Set up environment
cp .env.example .env
# Edit .env with production values

# Start services
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Seed universities
docker compose exec api python -m src.seeds.seed_universities
```

**Using Kubernetes:**

```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/web.yaml
kubectl apply -f k8s/ingress.yaml
```

### Frontend Deployment

**Vercel (Recommended):**

1. Connect GitHub repository to Vercel
2. Set environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://api.applymap.org
   NEXTAUTH_URL=https://applymap.org
   NEXTAUTH_SECRET=your-secret
   ```
3. Deploy

**Netlify:**

```bash
# Build
cd apps/web
pnpm build

# Deploy
netlify deploy --prod --dir=.next
```

### Database Setup

**PostgreSQL on AWS RDS:**

1. Create RDS instance (PostgreSQL 16)
2. Configure security groups
3. Update `DATABASE_URL` in environment
4. Run migrations

**Managed PostgreSQL:**

- **Supabase:** Free tier available
- **Neon:** Serverless PostgreSQL
- **Railway:** Simple deployment

---

## Monitoring & Maintenance

### Health Checks

**Backend:**
```bash
curl https://api.applymap.org/health
```

**Frontend:**
```bash
curl https://applymap.org
```

### Logs

**Docker:**
```bash
docker compose logs -f api
docker compose logs -f web
```

**Kubernetes:**
```bash
kubectl logs -f deployment/api -n applymap
kubectl logs -f deployment/web -n applymap
```

### Backups

**Database:**
```bash
# Backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20260510.sql
```

**User Data:**
```bash
# Export all user data (GDPR compliance)
docker compose exec api python -m src.scripts.export_user_data --user-id=<uuid>
```

---

## Scaling

### Horizontal Scaling

**Backend:**
- Add more API instances behind load balancer
- Use Redis for session storage
- Implement Celery for background tasks

**Frontend:**
- CDN for static assets (Cloudflare)
- Edge caching (Vercel Edge Network)
- Image optimization (Next.js Image)

### Vertical Scaling

**Database:**
- Increase instance size
- Add read replicas
- Enable connection pooling (PgBouncer)

**API:**
- Increase worker count (uvicorn --workers)
- Add more CPU/RAM
- Enable caching (Redis)

---

## Security Checklist

- [ ] HTTPS enabled (SSL certificate)
- [ ] Environment variables secured
- [ ] Database encrypted at rest
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (input sanitization)
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Regular dependency updates
- [ ] Backup strategy in place
- [ ] Monitoring and alerting set up

---

## Troubleshooting

### Common Issues

**1. Database connection failed**
```bash
# Check connection
psql $DATABASE_URL

# Verify credentials
echo $DATABASE_URL
```

**2. Gemini API errors**
```bash
# Check API key
curl -H "x-goog-api-key: $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models
```

**3. Frontend can't reach backend**
```bash
# Check CORS settings in apps/api/src/config.py
BACKEND_CORS_ORIGINS = ["https://applymap.org"]

# Verify API URL in frontend
echo $NEXT_PUBLIC_API_URL
```

**4. Migrations failed**
```bash
# Reset migrations (DANGER: data loss)
alembic downgrade base
alembic upgrade head

# Or create new migration
alembic revision --autogenerate -m "description"
```

---

## Performance Optimization

### Backend

1. **Enable caching:**
```python
# Add Redis caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="applymap")
```

2. **Database indexing:**
```sql
CREATE INDEX idx_achievements_user_id ON achievements(user_id);
CREATE INDEX idx_reports_user_id ON optimization_reports(user_id);
CREATE INDEX idx_universities_country ON universities(country);
```

3. **Connection pooling:**
```python
# In database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### Frontend

1. **Code splitting:**
```typescript
// Dynamic imports
const Dashboard = dynamic(() => import('./Dashboard'))
```

2. **Image optimization:**
```typescript
import Image from 'next/image'

<Image
  src="/logo.png"
  width={200}
  height={100}
  alt="ApplyMap"
  priority
/>
```

3. **API response caching:**
```typescript
// In TanStack Query
const { data } = useQuery({
  queryKey: ['universities'],
  queryFn: fetchUniversities,
  staleTime: 1000 * 60 * 5, // 5 minutes
})
```

---

## Cost Estimation

### Hugging Face (Free Tier)
- **Hosting:** Free
- **Compute:** CPU Basic (free)
- **Storage:** 50GB (free)
- **Bandwidth:** Unlimited
- **Total:** $0/month

### AWS (Production)
- **EC2 (t3.medium × 2):** $60/month
- **RDS (db.t3.small):** $30/month
- **S3 + CloudFront:** $10/month
- **Load Balancer:** $20/month
- **Total:** ~$120/month

### GCP (Production)
- **Cloud Run (API):** $40/month
- **Cloud SQL (PostgreSQL):** $35/month
- **Cloud Storage:** $5/month
- **Load Balancer:** $20/month
- **Total:** ~$100/month

### Vercel (Frontend)
- **Pro Plan:** $20/month
- **Bandwidth:** Included
- **Edge Functions:** Included
- **Total:** $20/month

**Total Production Cost:** ~$140/month

---

## Support & Resources

### Documentation
- **GitHub:** https://github.com/Galym7707/ApplyMap
- **README:** Comprehensive feature documentation
- **CLAUDE.md:** Architecture and development guide
- **MIT_SOLVE_ANALYSIS.md:** Full project analysis

### Community
- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** Community support
- **Email:** [To be added]

### Contributing
See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

**Last updated:** May 10, 2026  
**Version:** 1.0  
**Maintainer:** ApplyMap Team
