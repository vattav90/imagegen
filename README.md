# Image Generation Flask App

A Flask application that generates dynamic progress status images with customizable points and nights.

## API Endpoint

- **GET** `/generate-progress-image?points=<number>&nights=<number>`
  - Generates a PNG image showing progress toward Platinum Status
  - Parameters:
    - `points` (optional): Number of points (default: 0)
    - `nights` (optional): Number of nights (default: 0)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
python app.py
```

3. Access the app at `http://localhost:5000`

## Deployment Options

### Option 1: Heroku (Recommended)

Your app is already configured for Heroku with a `Procfile`.

1. **Install Heroku CLI** (if not already installed):
   - Visit: https://devcenter.heroku.com/articles/heroku-cli

2. **Login to Heroku**:
```bash
heroku login
```

3. **Create a new Heroku app**:
```bash
heroku create your-app-name
```

4. **Deploy**:
```bash
git init
git add .
git commit -m "Initial commit"
git push heroku main
```

5. **Open your app**:
```bash
heroku open
```

**Note**: If your default branch is `master` instead of `main`:
```bash
git push heroku master
```

### Option 2: Railway

1. **Install Railway CLI**:
```bash
npm i -g @railway/cli
```

2. **Login**:
```bash
railway login
```

3. **Initialize and deploy**:
```bash
railway init
railway up
```

4. Your app will be automatically deployed and you'll get a URL.

### Option 3: Render

1. Go to https://render.com and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click "Create Web Service"

### Option 4: PythonAnywhere

1. Sign up at https://www.pythonanywhere.com
2. Upload your files via Files tab
3. Go to Web tab and create a new web app
4. Set the source code path and WSGI configuration file
5. Update the WSGI file to point to your Flask app

### Option 5: DigitalOcean App Platform

1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App" → "GitHub"
3. Select your repository
4. Configure:
   - **Type**: Web Service
   - **Run Command**: `gunicorn app:app`
5. Deploy

## Environment Variables

The app uses the `PORT` environment variable (automatically set by most platforms). No additional configuration needed.

## Testing the Deployment

Once deployed, test your endpoint:
```
https://your-app-url.com/generate-progress-image?points=7000&nights=30
```

This should return a PNG image showing the progress visualization.

## Troubleshooting

- **Port issues**: The app automatically uses the `PORT` environment variable
- **Dependencies**: Make sure all packages in `requirements.txt` are installed
- **Image loading**: The app fetches images from external URLs; ensure your hosting platform allows outbound HTTP requests


