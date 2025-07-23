# Gigi AI Frontend Setup

## Overview
This is the professional frontend for Gigi AI built with Next.js, React, and TypeScript.

## Features
- 🎨 Professional landing page with gradient design
- 🔐 Login and Registration modals
- 📱 Responsive design for all devices
- 🚀 Smooth animations and transitions
- 🔒 Secure authentication with Django backend
- ⚡ Fast performance with Next.js

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Create environment file (.env.local):**
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NODE_ENV=development
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Django Backend Integration

The frontend is configured to work with your Django backend. Make sure your Django server is running on `http://localhost:8000` with the following API endpoints:

- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration  
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/me/` - Get current user
- `POST /api/auth/refresh/` - Refresh token

## File Structure
```
src/
├── app/
│   ├── globals.css      # Global styles
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Home page
├── components/
│   └── auth/
│       ├── LoginModal.tsx    # Login modal
│       └── RegisterModal.tsx # Registration modal
└── lib/
    └── auth.ts          # Authentication service
```

## Technologies Used
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **js-cookie** - Cookie management

## Production Build
```bash
npm run build
npm start
```

## Notes
- The authentication system uses JWT tokens stored in cookies
- All API calls are proxied through Next.js to handle CORS
- The design is mobile-first and fully responsive 