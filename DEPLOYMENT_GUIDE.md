# 📦 TFC Project - Production Deployment Guide

## 🚀 Quick Deploy to Render

### Prerequisites
- GitHub repository: `https://github.com/anisabdusamad-sys/tfc-project.git`
- Render account (free tier available)

---

## 🔧 Step 1: Deploy Main App (app.py)

### 1.1 Create New Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `anisabdusamad-sys/tfc-project`
4. Configure:
   - **Name**: `tfc-project` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
     ```
   - **Plan**: Free (or paid for production)

### 1.2 Environment Variables
Add these in Render's **Environment** tab:

```env
# Required
TFC_API_KEY=tfc_secret_key_2026_xyz_secure
FLASK_SECRET_KEY=change_this_to_random_secret_2026_production

# Optional (leave empty for auto-detection)
TFC_API_URL=
CLIENT_URL=
```

### 1.3 Deploy
- Click **"Create Web Service"**
- Wait for deployment (2-3 minutes)
- Your app will be live at: `https://tfc-project-XXXX.onrender.com`

---

## 🔧 Step 2: Deploy Admin Panel (bilol.py)

### 2.1 Create Another Web Service
1. Click **"New +"** → **"Web Service"**
2. Same GitHub repository
3. Configure:
   - **Name**: `tfc-admin`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     gunicorn bilol:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
     ```
   - **Plan**: Free

### 2.2 Environment Variables
```env
TFC_API_KEY=tfc_secret_key_2026_xyz_secure
TFC_API_URL=https://tfc-project-XXXX.onrender.com  # Replace with your app URL
ADMIN_API_KEY=admin_secure_key_2026_bilol
CLIENT_URL=https://tfc-project-XXXX.onrender.com
```

### 2.3 Deploy
- Click **"Create Web Service"**
- Admin panel will be at: `https://tfc-admin-XXXX.onrender.com`

---

## 🔄 Step 3: Update Cross-References

After both services are deployed:

### 3.1 Update app.py's ADMIN_HTML
Find this line in `app.py`:
```python
const BASE_URL = "https://tfc-project-2sss.onrender.com";
```

Replace with your actual Render URL:
```python
const BASE_URL = window.location.origin;  # Already done ✅
```

### 3.2 Update bilol.py's CLIENT_URL
In `.env` or Render environment:
```env
CLIENT_URL=https://tfc-project-XXXX.onrender.com
```

---

## ✅ Step 4: Verify Deployment

### 4.1 Test Main App
Visit: `https://tfc-project-XXXX.onrender.com`
- ✅ Auth screen appears
- ✅ Can login with name
- ✅ Menu loads with categories
- ✅ Can place test order

### 4.2 Test Admin Panel
Visit: `https://tfc-admin-XXXX.onrender.com`
- ✅ Admin login appears
- ✅ Enter password: `159951.tfc` (default)
- ✅ Orders tab shows test order
- ✅ Can update order status

### 4.3 Test Cross-Communication
1. Place order from main app
2. Check admin panel - order should appear within 3 seconds
3. Update status in admin
4. Main app should show notification

---

## 🔐 Security Checklist

- [x] API Keys are in environment variables (not hardcoded)
- [x] CORS configured for specific origins
- [x] SQL injection protection (parameterized queries)
- [x] XSS protection (HTML escaping in templates)
- [x] Admin panel password protected
- [ ] Change default admin password (`159951.tfc`)
- [ ] Change Flask secret key in production
- [ ] Enable HTTPS (automatic on Render)
- [ ] Set up custom domain (optional)

---

## 📊 Database Management

### SQLite on Render
- **Free tier**: Database is stored on ephemeral filesystem
- **⚠️ Important**: Data will be lost on redeploy!
- **Solution**: Use Render's Persistent Disks (paid) or external DB

### Backup Strategy
1. **Manual backup**: Download `.db` files from Render shell
2. **Automated backup**: Use Render's cron jobs to backup daily
3. **Production**: Upgrade to PostgreSQL on Render

---

## 🔄 Auto-Deploy Setup

### Enable Auto-Deploy
1. In Render dashboard, go to your service
2. **Settings** → **Auto-Deploy**
3. Toggle **"Auto-Deploy"** ON
4. Select branch: `main` or `master`

Now every push to GitHub will auto-deploy!

---

## 🐛 Troubleshooting

### Issue: "Module not found"
**Solution**: Check `requirements.txt` has all dependencies:
```txt
flask
flask-cors
python-dotenv
pywebpush
pillow
gunicorn
requests
```

### Issue: "Database locked"
**Solution**: Increase timeout in code (already done ✅):
```python
conn = sqlite3.connect(DB_PATH, timeout=20)
```

### Issue: "Port already in use"
**Solution**: Use Render's `$PORT` environment variable (already done ✅):
```python
port = int(os.environ.get("PORT", 5000))
```

### Issue: Admin panel can't connect to app
**Solution**: Check `TFC_API_URL` in bilol.py environment:
```env
TFC_API_URL=https://tfc-project-XXXX.onrender.com
```

---

## 📈 Scaling for Production

### When to Upgrade
- **Starter Plan** ($7/month): More RAM, no cold starts
- **Pro Plan** ($25/month): Dedicated resources, better performance

### Database Migration
1. Export SQLite data
2. Create PostgreSQL on Render
3. Update connection strings in code
4. Import data

### CDN for Images
Use Cloudflare or Render's CDN for static images:
```python
# In app.py
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache
```

---

## 🎯 Post-Deployment Checklist

- [ ] Both apps are live and accessible
- [ ] Can login to main app
- [ ] Can login to admin panel
- [ ] Orders sync between apps
- [ ] Push notifications work (if enabled)
- [ ] Images load correctly
- [ ] Mobile responsive (test on phone)
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (automatic on Render)
- [ ] Monitoring enabled in Render dashboard

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Project Issues**: https://github.com/anisabdusamad-sys/tfc-project/issues
- **Admin Password**: `159951.tfc` (change after first login!)

---

## 🎉 Success!

Your TFC project is now live! 🚀

**Main App**: `https://tfc-project-XXXX.onrender.com`  
**Admin Panel**: `https://tfc-admin-XXXX.onrender.com`

Share the main app URL with customers and start taking orders!