# Shopify Product Optimizer - Complete Setup Guide

## 📁 Required Files

Download and place these files in the same directory:

1. **flask_backend.py** - Backend server
2. **shopify_optimizer_ui.html** - Web interface  
3. **mainZ.py** - Your existing optimization script
4. **requirements.txt** - Python dependencies
5. **.env** - Your API credentials (create this file)

## 🔧 Installation Steps

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create .env File
Create a file named `.env` in the same directory with your API credentials:

```env
SHOPIFY_STORE_NAME=your-store-name.myshopify.com
SHOPIFY_ADMIN_TOKEN=shpat_your_admin_token_here
OPENAI_API_KEY=sk-your_openai_key_here
```

### Step 3: Start the Backend Server
```bash
python flask_backend.py
```

### Step 4: Access the Web Interface
Open your browser and go to: **http://localhost:5000**

## 🚀 Usage Guide

### Real Mode (Backend Connected)
- Click **"Preview Products"** to see actual products from your Shopify store
- Select fields to update
- Click **"Start Optimization"** to run the real optimization process
- Monitor progress in real-time

### Demo Mode (Backend Offline)  
- If the backend is not running, the UI automatically falls back to demo mode
- All functions work but use simulated data
- Perfect for testing the interface

## ⚙️ Configuration

### Settings Tab
- **API Configuration**: Enter your Shopify store, admin token, and OpenAI key
- **Google Trends**: Configure region (Denmark), language (Danish), enable/disable
- **Performance**: Adjust request delays, enable verbose logging
- **Data Management**: Export/import settings, clear cache

### Field Selection
Choose which product fields to update:
- ✅ **Product Title** - SEO optimized titles
- ✅ **Product Description** - Comprehensive HTML descriptions  
- ✅ **SEO Title** - Meta title tags
- ✅ **SEO Description** - Meta descriptions
- ⬜ **Product Type/Category** - Product categorization
- ⬜ **Vendor/Brand** - Brand assignment with rotation
- ⬜ **URL Handle** - SEO-friendly URLs

## 📊 Monitoring

### Real-time Stats
- **Products Found**: Total products with 'needs_update' tag
- **Processed**: Number of products completed
- **Success Rate**: Percentage of successful updates
- **Processing Time**: Elapsed time
- **Queue Length**: Remaining products
- **Trends Success Rate**: Google Trends data success rate

### Live Logs
- Color-coded log messages (success, error, warning, info)
- Real-time updates during processing
- Export logs for analysis
- Clear logs function

## 🔑 API Requirements

### Shopify Admin API
- Store name (your-store.myshopify.com)
- Admin API access token with product read/write permissions

### OpenAI API  
- Valid API key starting with 'sk-'
- GPT-4 access for best results

### Google Trends (Optional)
- No API key required
- Automatic rate limiting and retry logic
- Falls back gracefully if unavailable

## 🛠️ Troubleshooting

### Backend Won't Start
```bash
# Check if all dependencies are installed
pip install -r requirements.txt

# Verify .env file exists and has correct format
cat .env
```

### Shopify Connection Failed
- Verify store name format: `store-name.myshopify.com` (not just `store-name`)
- Check admin token has product read/write permissions
- Test connection using the "Test Connection" button

### OpenAI Connection Failed  
- Verify API key starts with `sk-`
- Check API key has sufficient credits
- Ensure GPT-4 access if using advanced features

### Google Trends Issues
- Rate limiting is normal - the system handles this automatically
- Some keywords may have no data - fallback keywords are used
- Disable trends if experiencing consistent issues

## 📈 Performance Tips

### For Large Product Catalogs
- Set product limits during testing (start with 5-10 products)
- Increase request delays if hitting rate limits
- Run during off-peak hours for better API availability

### For Better Google Trends Results
- Use common Danish product terms
- Process during European business hours
- Allow longer delays between requests (8+ seconds)

### Memory and Processing
- Backend processes products sequentially to avoid overload
- Each product takes 10-30 seconds depending on complexity
- Monitor system resources during large batch operations

## 🔒 Security Notes

- API credentials are stored in .env file (never commit to version control)
- Settings are saved locally in browser storage
- No sensitive data is transmitted to external services beyond required APIs
- Backend runs locally on your machine

## 📞 Support

If you encounter issues:
1. Check the browser console for JavaScript errors
2. Review backend terminal output for Python errors
3. Verify all files are in the same directory
4. Test API connections using the "Test Connection" button
5. Try demo mode first to verify UI functionality

## 🎯 Quick Start Checklist

- [ ] All 5 files downloaded and in same directory
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file created with your API credentials
- [ ] Backend started (`python flask_backend.py`)
- [ ] Browser opened to http://localhost:5000
- [ ] Settings configured in Settings tab
- [ ] Connection test passed
- [ ] Preview products works (shows real data)
- [ ] Ready to optimize!

## 🆕 New Features vs Original Script

### Enhanced UI Features
- **Visual Progress Tracking**: Real-time progress bars and statistics
- **Field Selection**: Choose exactly which fields to update
- **Connection Testing**: Verify all APIs before starting
- **Live Monitoring**: Watch optimization progress in real-time
- **Settings Management**: Save/load configurations
- **Demo Mode**: Test functionality without real data

### Improved Optimization
- **Better Google Trends Integration**: Smarter keyword extraction for Danish market
- **Enhanced Error Handling**: Graceful fallbacks and detailed error messages
- **Rate Limit Management**: Automatic delays and retry logic
- **Background Processing**: Non-blocking operations with real-time updates

### Additional Benefits
- **Web-based Interface**: No command-line knowledge required
- **Cross-platform**: Works on Windows, Mac, Linux
- **Portable**: Easy to share and deploy
- **Extensible**: Easy to add new features and integrations

## 🔄 Migration from Command Line

If you were using the original `mainZ.py` script:

### Before (Command Line)
```bash
python mainZ.py --fields title body_html seo_title seo_description --limit 10
```

### After (Web UI)
1. Open http://localhost:5000
2. Select fields: Product Title, Product Description, SEO Title, SEO Description
3. Set Product Limit: 10
4. Click "Start Optimization"
5. Monitor progress in real-time

### Advantages
- ✅ Visual feedback and progress tracking
- ✅ Real-time logs and error handling
- ✅ Easy field selection with descriptions
- ✅ Settings persistence across sessions
- ✅ Connection testing before processing
- ✅ Ability to stop/resume operations
- ✅ Export logs and settings for analysis

## 📊 File Structure

Your directory should look like this:
```
shopify-optimizer/
├── flask_backend.py           # Backend server
├── shopify_optimizer_ui.html  # Web interface
├── mainZ.py                   # Your optimization script
├── requirements.txt           # Python dependencies
├── .env                       # API credentials (create this)
└── SETUP_INSTRUCTIONS.md      # This guide
```

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Backend starts without errors
- ✅ Web UI loads at http://localhost:5000
- ✅ "Preview Products" shows real product count (not random)
- ✅ "Test Connection" passes for Shopify and OpenAI
- ✅ Settings save/load properly
- ✅ Optimization runs and shows real-time progress
- ✅ Products are actually updated in your Shopify store

## 💡 Pro Tips

### Keyboard Shortcuts
- **Ctrl+S**: Save settings
- **Ctrl+Shift+Enter**: Start/stop optimization
- **Tab**: Navigate between form fields

### Best Practices
1. **Always test with small batches first** (5-10 products)
2. **Use "Preview Products" before processing** to verify connection
3. **Monitor the logs during processing** for any issues
4. **Export settings and logs** for backup and analysis
5. **Run during off-peak hours** for better API performance

### Advanced Usage
- **Batch Processing**: Process large catalogs in smaller chunks
- **A/B Testing**: Test different field combinations
- **Performance Monitoring**: Track success rates and timing
- **Data Analysis**: Export logs for performance analysis

## 🔧 Customization Options

### Modifying Field Selection
Edit the `AVAILABLE_FIELDS` dictionary in `flask_backend.py` to add or remove fields.

### Changing Themes
Modify the CSS in `shopify_optimizer_ui.html` to customize colors and styling.

### Adding New Features
The modular design makes it easy to add new endpoints and UI components.

## 📈 Scaling Considerations

### For Enterprise Use
- Consider rate limiting for multiple concurrent users
- Implement user authentication if needed
- Add database logging for audit trails
- Monitor server resources during heavy usage

### For Multiple Stores
- Modify the backend to handle multiple store configurations
- Add store selection in the UI
- Implement separate .env files per store

Enjoy your enhanced Shopify Product Optimizer! 🚀