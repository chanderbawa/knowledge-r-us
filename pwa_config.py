#!/usr/bin/env python3
"""
Progressive Web App (PWA) configuration for Knowledge R Us
Adds mobile app-like experience to the Streamlit app
"""

import streamlit as st
import json

def add_pwa_config():
    """Add PWA configuration to make the app installable on mobile devices"""
    
    # PWA Manifest
    manifest = {
        "name": "Knowledge R Us - Educational News",
        "short_name": "Knowledge R Us",
        "description": "Educational news app with age-adaptive learning for kids",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#ff6b6b",
        "orientation": "portrait",
        "scope": "/",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3048/3048425.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3048/3048425.png", 
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable any"
            }
        ],
        "categories": ["education", "kids", "news", "learning"],
        "lang": "en",
        "dir": "ltr"
    }
    
    # Add manifest to page
    st.markdown(f"""
    <link rel="manifest" href="data:application/json;base64,{json.dumps(manifest).encode().hex()}">
    <meta name="theme-color" content="#ff6b6b">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Knowledge R Us">
    <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/3048/3048425.png">
    
    <!-- Mobile optimizations -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="mobile-web-app-capable" content="yes">
    
    <!-- Service Worker Registration -->
    <script>
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/sw.js')
                .then(function(registration) {{
                    console.log('SW registered: ', registration);
                }})
                .catch(function(registrationError) {{
                    console.log('SW registration failed: ', registrationError);
                }});
        }}
    </script>
    """, unsafe_allow_html=True)

def add_mobile_styles():
    """Add mobile-optimized CSS styles"""
    st.markdown("""
    <style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Make buttons touch-friendly */
        .stButton > button {
            height: 3rem;
            font-size: 1.1rem;
            border-radius: 10px;
        }
        
        /* Optimize form inputs for mobile */
        .stTextInput > div > div > input {
            font-size: 16px; /* Prevents zoom on iOS */
            height: 3rem;
        }
        
        .stSelectbox > div > div > select {
            font-size: 16px;
            height: 3rem;
        }
        
        /* Better spacing for mobile */
        .stExpander {
            margin-bottom: 1rem;
        }
        
        /* Touch-friendly radio buttons */
        .stRadio > div {
            gap: 1rem;
        }
        
        /* Optimize metrics display */
        .metric-container {
            text-align: center;
        }
        
        /* Better sidebar on mobile */
        .css-1d391kg {
            padding-top: 1rem;
        }
    }
    
    /* Improve touch targets */
    .stButton, .stDownloadButton {
        margin: 0.5rem 0;
    }
    
    /* Better visual feedback */
    .stButton > button:active {
        transform: scale(0.98);
        transition: transform 0.1s;
    }
    
    /* Optimize progress bars for mobile */
    .stProgress > div > div {
        height: 1rem;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

def create_service_worker():
    """Generate service worker content for offline functionality"""
    sw_content = """
const CACHE_NAME = 'knowledge-r-us-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
"""
    return sw_content

def add_install_prompt():
    """Add install prompt for PWA"""
    st.markdown("""
    <script>
    let deferredPrompt;
    
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        // Show install button
        const installButton = document.createElement('button');
        installButton.textContent = '📱 Install App';
        installButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
        `;
        
        installButton.addEventListener('click', () => {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                    installButton.remove();
                }
                deferredPrompt = null;
            });
        });
        
        document.body.appendChild(installButton);
    });
    </script>
    """, unsafe_allow_html=True)
