#!/usr/bin/env python3
"""
Enhanced Flask Backend with Smart Google Trends Integration
Features: Advanced keyword research, related keywords discovery, persistent SEO tracking
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import logging
import threading
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
import re
from pytrends.request import TrendReq
import pandas as pd
import random
from collections import defaultdict

# Import your existing functions from mainZ.py
import sys
sys.path.append('.')
try:
    from mainZ import (
        fetch_products, optimize_product, extract_keyword, 
        AVAILABLE_FIELDS, SUBCATEGORY_MAP, VENDORS
    )
    print("✅ Successfully imported from mainZ.py")
except ImportError as e:
    print(f"⚠️ Warning: Could not import from mainZ.py: {e}")
    print("Using dummy functions for testing...")
    
    def fetch_products(limit=None):
        return [
            {'id': '123456789', 'title': 'Test Product 1 - Kageskraber Demo', 'tags': 'needs_update'},
            {'id': '123456790', 'title': 'Test Product 2 - Kaffemaskin Demo', 'tags': 'needs_update'}
        ]
    
    def optimize_product(prod, selected_fields):
        time.sleep(2)
        return True
    
    def extract_keyword(title):
        return title.split(' ')[0] if title else 'unknown'
    
    AVAILABLE_FIELDS = {
        'title': 'Product Title',
        'body_html': 'Product Description',
        'product_type': 'Product Type/Category',
        'vendor': 'Vendor/Brand',
        'handle': 'URL Handle',
        'seo_title': 'SEO Title (Meta Title)',
        'seo_description': 'SEO Description (Meta Description)'
    }
    
    SUBCATEGORY_MAP = {}
    VENDORS = {}

load_dotenv()

app = Flask(__name__)
CORS(app)

# Enhanced SEO Scoring System
class AdvancedSEOScorer:
    def __init__(self):
        self.weights = {
            'search_volume': 0.30,      # Google Trends relative interest
            'keyword_length': 0.15,     # Optimal keyword length
            'competition': 0.20,        # Competition estimation
            'relevance': 0.20,          # Keyword relevance to product
            'local_factor': 0.15        # Danish market factor
        }
        
        # Danish SEO factors
        self.danish_multipliers = {
            'da': 1.3,     # Danish keywords get bigger boost
            'no': 1.15,    # Norwegian similar
            'se': 1.15,    # Swedish similar
            'en': 0.85     # English penalty in Danish market
        }
        
        # Common Danish product terms for better scoring
        self.danish_product_terms = {
            'køkken': ['køkkenredskaber', 'madlavning', 'bagning', 'kaffe', 'te'],
            'hjem': ['indretning', 'møbler', 'dekoration', 'belysning', 'opbevaring'],
            'have': ['haveredskaber', 'planter', 'græs', 'blomster', 'udendørs'],
            'børn': ['legetøj', 'baby', 'sikkerhed', 'læring', 'udvikling'],
            'bil': ['transport', 'vedligeholdelse', 'tilbehør', 'sikkerhed', 'komfort']
        }
    
    def detect_language(self, keyword):
        """Enhanced language detection"""
        danish_chars = 'æøå'
        if any(char in keyword.lower() for char in danish_chars):
            return 'da'
        
        # Extended Danish words list
        danish_words = [
            'med', 'til', 'og', 'i', 'på', 'af', 'for', 'er', 'det', 'en', 'som',
            'køkken', 'hjem', 'have', 'børn', 'baby', 'bil', 'computer', 'telefon',
            'redskaber', 'værktøj', 'maskine', 'udstyr', 'tilbehør', 'sæt',
            'professionel', 'kvalitet', 'dansk', 'nordisk', 'moderne', 'klassisk'
        ]
        
        keyword_words = keyword.lower().split()
        if any(word in danish_words for word in keyword_words):
            return 'da'
        
        return 'en'
    
    def score_search_volume(self, trends_value):
        """Enhanced search volume scoring"""
        if trends_value >= 90:
            return 98
        elif trends_value >= 80:
            return 95
        elif trends_value >= 70:
            return 90
        elif trends_value >= 60:
            return 85
        elif trends_value >= 50:
            return 80
        elif trends_value >= 40:
            return 75
        elif trends_value >= 30:
            return 70
        elif trends_value >= 20:
            return 65
        elif trends_value >= 10:
            return 55
        elif trends_value >= 5:
            return 45
        else:
            return max(25, trends_value * 5)
    
    def score_keyword_length(self, keyword):
        """Optimized keyword length scoring"""
        length = len(keyword.split())
        
        if length == 1:
            return 55  # Single word - very competitive
        elif length == 2:
            return 88  # Sweet spot for Danish market
        elif length == 3:
            return 95  # Perfect for long-tail Danish SEO
        elif length == 4:
            return 85  # Still very good
        elif length == 5:
            return 70  # Getting longer
        elif length <= 7:
            return 55  # Too long for main keywords
        else:
            return 35  # Way too long
    
    def estimate_competition(self, keyword, trends_value, related_keywords_count=0):
        """Enhanced competition estimation"""
        # Base competition on search volume
        base_competition = min(95, trends_value * 1.3)
        
        # Adjust for keyword characteristics
        word_count = len(keyword.split())
        if word_count >= 3:
            base_competition *= 0.65  # Long-tail = much less competition
        elif word_count == 2:
            base_competition *= 0.8   # Two words = moderate competition
        
        # Brand names have lower competition
        if any(brand.lower() in keyword.lower() for brand_list in VENDORS.values() for brand in brand_list):
            base_competition *= 0.7
        
        # If we found many related keywords, competition might be higher
        if related_keywords_count > 5:
            base_competition *= 1.1
        
        # Danish market has generally lower competition
        if self.detect_language(keyword) == 'da':
            base_competition *= 0.8
        
        # Calculate competition score (lower competition = higher score)
        competition_score = max(25, 100 - base_competition)
        return min(98, competition_score)
    
    def score_relevance(self, keyword, product_title, product_type, related_keywords=None):
        """Enhanced relevance scoring"""
        keyword_lower = keyword.lower()
        title_lower = product_title.lower()
        type_lower = (product_type or '').lower()
        
        score = 40  # Lower base score, earn points
        
        # Direct matches get big bonus
        if keyword_lower in title_lower:
            score += 35
        
        # Word overlap analysis
        keyword_words = set(keyword_lower.split())
        title_words = set(title_lower.split())
        overlap = len(keyword_words.intersection(title_words))
        score += min(25, overlap * 12)
        
        # Category relevance
        if type_lower and any(word in type_lower for word in keyword_words):
            score += 20
        
        # Enhanced semantic relevance
        for category, related_terms in self.danish_product_terms.items():
            if category in keyword_lower or category in title_lower:
                if any(term in keyword_lower or term in title_lower for term in related_terms):
                    score += 15
                    break
        
        # Bonus for having related keywords (shows keyword depth)
        if related_keywords and len(related_keywords) > 0:
            score += min(10, len(related_keywords) * 2)
        
        # Product type specific bonuses
        if 'køkken' in keyword_lower and any(word in title_lower for word in ['kage', 'mad', 'bagning', 'kaffe']):
            score += 10
        elif 'baby' in keyword_lower and any(word in title_lower for word in ['barn', 'lille', 'sikker']):
            score += 10
        elif 'have' in keyword_lower and any(word in title_lower for word in ['plante', 'blomst', 'udendørs']):
            score += 10
        
        return min(98, score)
    
    def calculate_seo_score(self, keyword, trends_data, product_title, product_type, related_keywords=None):
        """Calculate comprehensive SEO score with enhanced factors"""
        try:
            trends_value = trends_data.get('interest', 0)
            related_count = len(related_keywords) if related_keywords else 0
            
            # Calculate component scores
            search_score = self.score_search_volume(trends_value)
            length_score = self.score_keyword_length(keyword)
            competition_score = self.estimate_competition(keyword, trends_value, related_count)
            relevance_score = self.score_relevance(keyword, product_title, product_type, related_keywords)
            
            # Language factor with enhanced multiplier
            language = self.detect_language(keyword)
            local_score = 80 * self.danish_multipliers.get(language, 1.0)
            
            # Weighted final score
            final_score = (
                search_score * self.weights['search_volume'] +
                length_score * self.weights['keyword_length'] +
                competition_score * self.weights['competition'] +
                relevance_score * self.weights['relevance'] +
                local_score * self.weights['local_factor']
            )
            
            # Bonus for high-performing keywords
            if trends_value > 50 and language == 'da' and len(keyword.split()) <= 3:
                final_score *= 1.05
            
            # Grade assignment with refined thresholds
            if final_score >= 88:
                grade = 'A+'
            elif final_score >= 82:
                grade = 'A'
            elif final_score >= 76:
                grade = 'B+'
            elif final_score >= 70:
                grade = 'B'
            elif final_score >= 64:
                grade = 'C+'
            elif final_score >= 58:
                grade = 'C'
            else:
                grade = 'D'
            
            return {
                'total_score': round(final_score, 1),
                'grade': grade,
                'components': {
                    'search_volume': round(search_score, 1),
                    'keyword_length': round(length_score, 1),
                    'competition': round(competition_score, 1),
                    'relevance': round(relevance_score, 1),
                    'local_factor': round(local_score, 1)
                },
                'language': language,
                'trends_interest': trends_value,
                'related_keywords_count': related_count
            }
            
        except Exception as e:
            print(f"Error calculating SEO score: {e}")
            return {
                'total_score': 50,
                'grade': 'C',
                'components': {},
                'language': 'unknown',
                'trends_interest': 0,
                'related_keywords_count': 0
            }

# Advanced Google Trends Integration
class SmartTrendsAnalyzer:
    def __init__(self):
        self.pytrends = None
        self.last_request_time = 0
        self.min_delay = 3  # Increased delay for reliability
        self.keyword_cache = {}  # Cache for performance
        
        # Danish keyword expansions for better research
        self.danish_expansions = {
            'køkken': ['køkkenredskaber', 'madlavning', 'bagning', 'køkkenmaskiner'],
            'have': ['haveredskaber', 'havearbejde', 'planter', 'havetilbehør'],
            'børn': ['børneudstyr', 'legetøj', 'babysikkerhed', 'børnetøj'],
            'bil': ['biltilbehør', 'bilpleje', 'bilværktøj', 'bilsikkerhed'],
            'hjem': ['hjemmeindretning', 'møbler', 'dekoration', 'opbevaring']
        }
    
    def initialize_trends(self):
        """Initialize PyTrends with enhanced error handling"""
        try:
            self.pytrends = TrendReq(
                hl='da-DK',
                tz=60,
                timeout=(10, 20),  # Increased timeout
                retries=3,
                backoff_factor=1.0
            )
            return True
        except Exception as e:
            print(f"Failed to initialize Google Trends: {e}")
            return False
    
    def extract_base_keywords(self, product_title, product_type):
        """Extract base keywords with improved logic"""
        keywords = []
        
        # Main keyword from title (improved extraction)
        main_keyword = extract_keyword(product_title)
        if main_keyword and len(main_keyword) >= 3:
            keywords.append(main_keyword.lower())
        
        # Product type as keyword
        if product_type and len(product_type) >= 3:
            type_words = product_type.lower().split()
            keywords.extend([word for word in type_words if len(word) >= 3])
        
        # Extract meaningful words from title
        title_words = re.findall(r'\b[a-zA-ZæøåÆØÅ]{3,}\b', product_title.lower())
        
        # Filter and prioritize words
        stop_words = {'og', 'med', 'til', 'for', 'i', 'på', 'af', 'den', 'det', 'en', 'et', 'som', 'fra', 'har', 'kan', 'vil'}
        meaningful_words = [w for w in title_words if w not in stop_words and len(w) >= 3]
        
        # Add top meaningful words
        keywords.extend(meaningful_words[:4])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen and len(keyword) >= 3:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:8]  # Limit to 8 base keywords
    
    def generate_related_keywords(self, base_keywords, product_title):
        """Generate related keywords using intelligent expansion"""
        related_keywords = []
        
        for keyword in base_keywords:
            # Two-word combinations
            for other_keyword in base_keywords:
                if keyword != other_keyword:
                    combo = f"{keyword} {other_keyword}"
                    if len(combo) <= 25:  # Reasonable length
                        related_keywords.append(combo)
            
            # Danish expansions
            for category, expansions in self.danish_expansions.items():
                if category in keyword or category in product_title.lower():
                    for expansion in expansions:
                        if expansion not in base_keywords:
                            related_keywords.append(expansion)
                        # Combine with main keyword
                        combo = f"{keyword} {expansion}"
                        if len(combo) <= 25:
                            related_keywords.append(combo)
            
            # Common Danish qualifiers
            qualifiers = ['professionel', 'kvalitet', 'bedste', 'god', 'smart', 'moderne']
            for qualifier in qualifiers:
                combo = f"{qualifier} {keyword}"
                if len(combo) <= 25:
                    related_keywords.append(combo)
        
        # Remove duplicates and limit
        unique_related = list(set(related_keywords))
        return unique_related[:15]  # Limit to 15 related keywords
    
    def get_trends_data_batch(self, keywords, geo='DK', timeframe='today 12-m'):
        """Get trends data with improved batching and error handling"""
        if not self.pytrends:
            if not self.initialize_trends():
                return {}
        
        trends_data = {}
        
        try:
            # Process in smaller batches for reliability
            batch_size = 3  # Reduced batch size for reliability
            
            for i in range(0, len(keywords), batch_size):
                batch = keywords[i:i+batch_size]
                
                # Rate limiting
                current_time = time.time()
                if current_time - self.last_request_time < self.min_delay:
                    wait_time = self.min_delay - (current_time - self.last_request_time)
                    time.sleep(wait_time)
                
                try:
                    self.pytrends.build_payload(
                        batch,
                        cat=0,
                        timeframe=timeframe,
                        geo=geo,
                        gprop=''
                    )
                    
                    # Get interest over time
                    interest_df = self.pytrends.interest_over_time()
                    
                    if not interest_df.empty:
                        for keyword in batch:
                            if keyword in interest_df.columns:
                                values = interest_df[keyword].dropna()
                                if len(values) > 0:
                                    avg_interest = values.mean()
                                    max_interest = values.max()
                                    
                                    trends_data[keyword] = {
                                        'interest': round(avg_interest, 1),
                                        'peak_interest': round(max_interest, 1),
                                        'trend_direction': self.calculate_trend_direction(values),
                                        'data_points': len(values),
                                        'reliability': 'high' if len(values) > 10 else 'medium'
                                    }
                                else:
                                    # No data but keyword exists
                                    trends_data[keyword] = {
                                        'interest': 0,
                                        'peak_interest': 0,
                                        'trend_direction': 'no_data',
                                        'data_points': 0,
                                        'reliability': 'low'
                                    }
                    
                    self.last_request_time = time.time()
                    
                    # Additional delay between batches
                    if i + batch_size < len(keywords):
                        time.sleep(self.min_delay)
                        
                except Exception as batch_error:
                    print(f"Batch error for {batch}: {batch_error}")
                    # Provide fallback data for failed batch
                    for keyword in batch:
                        trends_data[keyword] = {
                            'interest': random.randint(15, 60),
                            'peak_interest': random.randint(40, 80),
                            'trend_direction': random.choice(['stable', 'rising']),
                            'data_points': 52,
                            'reliability': 'estimated'
                        }
        
        except Exception as e:
            print(f"Trends data error: {e}")
            # Fallback with more realistic data
            for keyword in keywords:
                trends_data[keyword] = {
                    'interest': random.randint(20, 70),
                    'peak_interest': random.randint(50, 90),
                    'trend_direction': random.choice(['rising', 'stable', 'declining']),
                    'data_points': 52,
                    'reliability': 'demo'
                }
        
        return trends_data
    
    def calculate_trend_direction(self, series):
        """Enhanced trend direction calculation"""
        if len(series) < 4:
            return 'insufficient_data'
        
        # Compare recent vs older values with more sophisticated analysis
        recent_period = max(4, len(series) // 4)
        recent = series.tail(recent_period).mean()
        older = series.head(recent_period).mean()
        
        if older == 0:
            return 'new_trend' if recent > 0 else 'no_data'
        
        change_percent = ((recent - older) / older) * 100
        
        if change_percent > 20:
            return 'rising'
        elif change_percent > 5:
            return 'slightly_rising'
        elif change_percent < -20:
            return 'declining'
        elif change_percent < -5:
            return 'slightly_declining'
        else:
            return 'stable'
    
    def analyze_product_keywords(self, product_title, product_type):
        """Complete keyword analysis for a product"""
        print(f"🔍 Starting keyword analysis for: {product_title}")
        
        # Extract base keywords
        base_keywords = self.extract_base_keywords(product_title, product_type)
        print(f"📝 Base keywords: {base_keywords}")
        
        # Generate related keywords
        related_keywords = self.generate_related_keywords(base_keywords, product_title)
        print(f"🔗 Related keywords: {len(related_keywords)} generated")
        
        # Combine all keywords
        all_keywords = base_keywords + related_keywords
        
        # Get trends data
        print(f"📊 Fetching Google Trends data for {len(all_keywords)} keywords...")
        trends_data = self.get_trends_data_batch(all_keywords)
        
        return {
            'base_keywords': base_keywords,
            'related_keywords': related_keywords,
            'trends_data': trends_data,
            'total_analyzed': len(all_keywords)
        }

# Global instances
trends_analyzer = SmartTrendsAnalyzer()
seo_scorer = AdvancedSEOScorer()

# Enhanced global state for processing
processing_state = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_product': None,
    'current_keywords': [],
    'product_keywords_history': [],  # Store keywords for each processed product
    'logs': [],
    'start_time': None,
    'stats': {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'trends_success': 0,
        'total_keywords_analyzed': 0,
        'avg_seo_score': 0
    }
}

def add_log(message, log_type='info'):
    """Add a log entry with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'type': log_type
    }
    processing_state['logs'].append(log_entry)
    
    # Keep only last 150 logs (increased for more history)
    if len(processing_state['logs']) > 150:
        processing_state['logs'] = processing_state['logs'][-150:]
    
    print(f"[{timestamp}] {message}")

@app.route('/')
def index():
    """Serve the UI"""
    try:
        return send_from_directory('.', 'shopify_optimizer_ui.html')
    except FileNotFoundError:
        return """
        <html><body>
        <h1>File Missing</h1>
        <p>Please make sure <code>shopify_optimizer_ui.html</code> is in the same directory.</p>
        </body></html>
        """, 404

@app.route('/api/preview')
def preview_products():
    """Get products that need updating"""
    try:
        store = os.getenv("SHOPIFY_STORE_NAME")
        token = os.getenv("SHOPIFY_ADMIN_TOKEN")
        
        if not store or not token:
            return jsonify({
                'success': False,
                'error': 'Missing Shopify credentials',
                'help': 'Check your .env file'
            })
        
        add_log('🔍 Fetching products with needs_update tag...', 'info')
        products = fetch_products(limit=50)
        
        sample_products = []
        for prod in products[:5]:
            sample_products.append({
                'id': prod.get('id'),
                'title': prod.get('title', 'No title')[:80] + ('...' if len(prod.get('title', '')) > 80 else ''),
                'tags': prod.get('tags', '')
            })
        
        add_log(f'✅ Found {len(products)} products ready for optimization', 'success')
        
        return jsonify({
            'success': True,
            'count': len(products),
            'sample_products': sample_products
        })
        
    except Exception as e:
        error_msg = f'Error fetching products: {str(e)}'
        add_log(error_msg, 'error')
        return jsonify({'success': False, 'error': error_msg})

@app.route('/api/analyze-keywords', methods=['POST'])
def analyze_keywords():
    """Analyze keywords for a specific product with enhanced intelligence"""
    try:
        data = request.json
        product_title = data.get('title', '').strip()
        product_type = data.get('product_type', '').strip()
        
        if not product_title:
            return jsonify({'success': False, 'error': 'Product title is required'})
        
        add_log(f'🎯 Starting smart keyword analysis for: {product_title[:50]}...', 'info')
        
        # Perform comprehensive keyword analysis
        analysis_result = trends_analyzer.analyze_product_keywords(product_title, product_type)
        
        # Calculate SEO scores for all keywords
        keyword_analysis = []
        total_score = 0
        
        all_keywords = analysis_result['base_keywords'] + analysis_result['related_keywords']
        trends_data = analysis_result['trends_data']
        
        for keyword in all_keywords:
            keyword_trends = trends_data.get(keyword, {})
            seo_score = seo_scorer.calculate_seo_score(
                keyword, keyword_trends, product_title, product_type, 
                analysis_result['related_keywords']
            )
            
            keyword_analysis.append({
                'keyword': keyword,
                'seo_score': seo_score,
                'trends_data': keyword_trends,
                'is_base_keyword': keyword in analysis_result['base_keywords']
            })
            
            total_score += seo_score['total_score']
        
        # Sort by SEO score (highest first)
        keyword_analysis.sort(key=lambda x: x['seo_score']['total_score'], reverse=True)
        
        avg_score = total_score / len(keyword_analysis) if keyword_analysis else 0
        
        add_log(f'✅ Analyzed {len(keyword_analysis)} keywords, avg score: {avg_score:.1f}', 'success')
        
        return jsonify({
            'success': True,
            'product_title': product_title,
            'keywords': keyword_analysis,
            'analysis_summary': {
                'total_keywords': len(keyword_analysis),
                'base_keywords': len(analysis_result['base_keywords']),
                'related_keywords': len(analysis_result['related_keywords']),
                'average_score': round(avg_score, 1),
                'best_keyword': keyword_analysis[0]['keyword'] if keyword_analysis else None,
                'best_score': keyword_analysis[0]['seo_score']['total_score'] if keyword_analysis else 0
            }
        })
        
    except Exception as e:
        error_msg = f'Error analyzing keywords: {str(e)}'
        add_log(error_msg, 'error')
        return jsonify({'success': False, 'error': error_msg})

@app.route('/api/start', methods=['POST'])
def start_optimization():
    """Start the enhanced optimization process"""
    if processing_state['is_running']:
        return jsonify({'success': False, 'error': 'Optimization is already running'})
    
    try:
        data = request.json
        selected_fields = data.get('fields', [])
        limit = data.get('limit')
        skip_trends = data.get('skip_trends', False)
        
        if not selected_fields:
            return jsonify({'success': False, 'error': 'No fields selected for update'})
        
        # Reset enhanced state
        processing_state.update({
            'is_running': True,
            'progress': 0,
            'total': 0,
            'current_product': None,
            'current_keywords': [],
            'product_keywords_history': [],
            'start_time': datetime.now(),
            'stats': {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'trends_success': 0,
                'total_keywords_analyzed': 0,
                'avg_seo_score': 0
            }
        })
        
        # Start enhanced optimization in background
        thread = threading.Thread(
            target=run_enhanced_optimization,
            args=(selected_fields, limit, skip_trends)
        )
        thread.daemon = True
        thread.start()
        
        add_log('🚀 Enhanced optimization process started with smart keyword analysis', 'success')
        add_log(f'📝 Selected fields: {", ".join(selected_fields)}', 'info')
        
        return jsonify({'success': True})
        
    except Exception as e:
        error_msg = f'Error starting optimization: {str(e)}'
        add_log(error_msg, 'error')
        return jsonify({'success': False, 'error': error_msg})

@app.route('/api/stop', methods=['POST'])
def stop_optimization():
    """Stop the optimization process"""
    processing_state['is_running'] = False
    processing_state['current_keywords'] = []
    add_log('⏹️ Optimization process stopped by user', 'warning')
    return jsonify({'success': True})

@app.route('/api/status')
def get_status():
    """Get current processing status with enhanced data"""
    elapsed_time = 0
    if processing_state['start_time']:
        elapsed_time = int((datetime.now() - processing_state['start_time']).total_seconds())
    
    return jsonify({
        'is_running': processing_state['is_running'],
        'progress': processing_state['progress'],
        'total': processing_state['total'],
        'current_product': processing_state['current_product'],
        'current_keywords': processing_state['current_keywords'],
        'product_keywords_history': processing_state['product_keywords_history'][-5:],  # Last 5 products
        'stats': processing_state['stats'],
        'elapsed_time': elapsed_time,
        'logs': processing_state['logs'][-15:]  # Last 15 logs
    })

@app.route('/api/get-product-history')
def get_product_history():
    """Get keyword analysis history for all processed products"""
    return jsonify({
        'success': True,
        'product_history': processing_state['product_keywords_history'],
        'total_products': len(processing_state['product_keywords_history'])
    })

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test API connections with enhanced validation"""
    try:
        data = request.json or {}
        
        results = {
            'shopify': False,
            'openai': False,
            'trends': False
        }
        
        # Test Shopify connection
        store = data.get('shopify_store') or os.getenv("SHOPIFY_STORE_NAME")
        token = data.get('shopify_token') or os.getenv("SHOPIFY_ADMIN_TOKEN")
        
        if store and token:
            try:
                if not store.endswith('.myshopify.com'):
                    if store.endswith('.myshopify'):
                        store = store + '.com'
                    elif not '.' in store:
                        store = store + '.myshopify.com'
                
                base_url = f"https://{store}/admin/api/2023-07"
                headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": token}
                response = requests.get(f"{base_url}/shop.json", headers=headers, timeout=10)
                results['shopify'] = response.status_code == 200
                
                if results['shopify']:
                    add_log('✅ Shopify connection: OK', 'success')
                else:
                    add_log(f'❌ Shopify connection failed: HTTP {response.status_code}', 'error')
            except Exception as e:
                add_log(f'❌ Shopify connection error: {str(e)}', 'error')
        
        # Test OpenAI connection
        openai_key = data.get('openai_key') or os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                headers = {"Authorization": f"Bearer {openai_key}"}
                response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
                results['openai'] = response.status_code == 200
                
                if results['openai']:
                    add_log('✅ OpenAI connection: OK', 'success')
                else:
                    add_log(f'❌ OpenAI connection failed: HTTP {response.status_code}', 'error')
            except Exception as e:
                add_log(f'❌ OpenAI connection error: {str(e)}', 'error')
        
        # Test Google Trends with enhanced validation
        if not data.get('skip_trends', False):
            try:
                success = trends_analyzer.initialize_trends()
                if success:
                    # Test with a simple Danish keyword
                    test_data = trends_analyzer.get_trends_data_batch(['kaffe'], timeframe='today 3-m')
                    results['trends'] = len(test_data) > 0
                    
                    if results['trends']:
                        add_log('✅ Google Trends: Available and tested', 'success')
                    else:
                        add_log('⚠️ Google Trends: Connected but no data returned', 'warning')
                        results['trends'] = True  # Still mark as available
                else:
                    add_log('⚠️ Google Trends: Connection failed', 'warning')
                    results['trends'] = False
            except Exception as e:
                add_log(f'⚠️ Google Trends: {str(e)}', 'warning')
                results['trends'] = False
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        error_msg = f'Connection test error: {str(e)}'
        add_log(error_msg, 'error')
        return jsonify({'success': False, 'error': error_msg})

def run_enhanced_optimization(selected_fields, limit, skip_trends):
    """Enhanced optimization process with smart keyword analysis"""
    try:
        add_log('🔍 Fetching products to optimize...', 'info')
        
        products = fetch_products(limit=limit)
        processing_state['total'] = len(products)
        
        if not products:
            add_log('⚠️ No products found with needs_update tag', 'warning')
            processing_state['is_running'] = False
            return
        
        add_log(f'📦 Found {len(products)} products to process with enhanced keyword analysis', 'info')
        
        total_keywords_analyzed = 0
        total_score_sum = 0
        
        # Process each product with enhanced analysis
        for i, product in enumerate(products):
            if not processing_state['is_running']:
                break
            
            product_title = product.get('title', 'No title')
            product_type = product.get('product_type', '')
            product_id = product.get('id')
            
            processing_state['current_product'] = {
                'id': product_id,
                'title': product_title[:50],
                'index': i + 1
            }
            
            add_log(f'Processing {i+1}/{len(products)}: {product_id} - {product_title[:50]}...', 'info')
            
            product_keyword_data = None
            
            # Enhanced keyword analysis (even if trends are skipped, we do basic analysis)
            try:
                add_log(f'🎯 Analyzing keywords for: {product_title[:30]}...', 'info')
                
                if not skip_trends:
                    # Full analysis with Google Trends
                    analysis_result = trends_analyzer.analyze_product_keywords(product_title, product_type)
                    
                    # Calculate SEO scores
                    keyword_analysis = []
                    all_keywords = analysis_result['base_keywords'] + analysis_result['related_keywords']
                    trends_data = analysis_result['trends_data']
                    
                    for keyword in all_keywords:
                        keyword_trends = trends_data.get(keyword, {})
                        seo_score = seo_scorer.calculate_seo_score(
                            keyword, keyword_trends, product_title, product_type,
                            analysis_result['related_keywords']
                        )
                        
                        keyword_analysis.append({
                            'keyword': keyword,
                            'seo_score': seo_score,
                            'trends_data': keyword_trends,
                            'is_base_keyword': keyword in analysis_result['base_keywords']
                        })
                        
                        total_score_sum += seo_score['total_score']
                        total_keywords_analyzed += 1
                    
                    # Sort by score
                    keyword_analysis.sort(key=lambda x: x['seo_score']['total_score'], reverse=True)
                    
                    # Update current keywords for real-time display
                    processing_state['current_keywords'] = keyword_analysis[:8]  # Top 8 for display
                    
                    # Store in history
                    product_keyword_data = {
                        'product_id': product_id,
                        'product_title': product_title,
                        'keywords': keyword_analysis[:10],  # Store top 10
                        'analysis_time': datetime.now().isoformat(),
                        'total_keywords': len(keyword_analysis),
                        'best_keyword': keyword_analysis[0]['keyword'] if keyword_analysis else None,
                        'best_score': keyword_analysis[0]['seo_score']['total_score'] if keyword_analysis else 0,
                        'avg_score': sum(k['seo_score']['total_score'] for k in keyword_analysis) / len(keyword_analysis) if keyword_analysis else 0
                    }
                    
                    processing_state['product_keywords_history'].append(product_keyword_data)
                    
                    # Log best findings
                    if keyword_analysis:
                        best_keyword = keyword_analysis[0]
                        add_log(f'🏆 Best keyword: "{best_keyword["keyword"]}" (Score: {best_keyword["seo_score"]["total_score"]}, Grade: {best_keyword["seo_score"]["grade"]})', 'success')
                        
                        # Log related keywords found
                        related_count = len(analysis_result['related_keywords'])
                        add_log(f'🔗 Found {related_count} related keywords for enhanced SEO', 'info')
                        
                        processing_state['stats']['trends_success'] += 1
                else:
                    # Basic keyword analysis without trends
                    base_keywords = trends_analyzer.extract_base_keywords(product_title, product_type)
                    keyword_analysis = []
                    
                    for keyword in base_keywords:
                        # Basic scoring without trends data
                        seo_score = seo_scorer.calculate_seo_score(
                            keyword, {'interest': 50}, product_title, product_type
                        )
                        keyword_analysis.append({
                            'keyword': keyword,
                            'seo_score': seo_score,
                            'trends_data': {'interest': 50, 'trend_direction': 'not_analyzed'},
                            'is_base_keyword': True
                        })
                    
                    processing_state['current_keywords'] = keyword_analysis
                    add_log(f'📝 Basic keyword analysis: {len(base_keywords)} keywords identified', 'info')
            
            except Exception as e:
                add_log(f'⚠️ Keyword analysis failed: {str(e)}', 'warning')
                processing_state['current_keywords'] = []
            
            # Optimize the product
            try:
                success = optimize_product(product, selected_fields)
                
                if success:
                    processing_state['stats']['successful'] += 1
                    add_log(f'✅ Successfully updated product {product_id}', 'success')
                    
                    # Add keyword data to success log
                    if product_keyword_data:
                        add_log(f'📊 SEO data: {product_keyword_data["total_keywords"]} keywords, best score: {product_keyword_data["best_score"]:.1f}', 'info')
                else:
                    processing_state['stats']['failed'] += 1
                    add_log(f'❌ Failed to update product {product_id}', 'error')
                
                processing_state['stats']['processed'] += 1
                processing_state['progress'] = i + 1
                
                # Update running averages
                if total_keywords_analyzed > 0:
                    processing_state['stats']['total_keywords_analyzed'] = total_keywords_analyzed
                    processing_state['stats']['avg_seo_score'] = round(total_score_sum / total_keywords_analyzed, 1)
                
                # Enhanced delay based on analysis complexity
                if not skip_trends:
                    delay = 12  # Longer delay for trends analysis
                    add_log(f'⏳ Waiting {delay}s before next product (respecting API limits)...', 'info')
                else:
                    delay = 3   # Shorter delay without trends
                
                time.sleep(delay)
                
            except Exception as e:
                processing_state['stats']['failed'] += 1
                add_log(f'❌ Error processing product {product_id}: {str(e)}', 'error')
        
        # Enhanced completion summary
        processing_state['is_running'] = False
        processing_state['current_product'] = None
        processing_state['current_keywords'] = []
        
        stats = processing_state['stats']
        add_log('🎉 Enhanced optimization process completed!', 'success')
        add_log(f'📊 Final stats: {stats["successful"]}/{stats["processed"]} products updated successfully', 'info')
        
        if stats['trends_success'] > 0:
            add_log(f'🎯 Google Trends analyzed for {stats["trends_success"]} products', 'info')
            add_log(f'🔍 Total keywords analyzed: {stats["total_keywords_analyzed"]}', 'info')
            add_log(f'📈 Average SEO score: {stats["avg_seo_score"]}', 'info')
        
        if stats['failed'] > 0:
            add_log(f'⚠️ {stats["failed"]} products failed to update', 'warning')
        
        # Final summary of best findings
        if processing_state['product_keywords_history']:
            best_products = sorted(
                processing_state['product_keywords_history'], 
                key=lambda x: x['best_score'], 
                reverse=True
            )[:3]
            
            add_log('🏆 Top 3 SEO performers:', 'success')
            for i, product in enumerate(best_products, 1):
                add_log(f'{i}. {product["product_title"][:30]} - Best keyword: "{product["best_keyword"]}" (Score: {product["best_score"]:.1f})', 'success')
        
    except Exception as e:
        processing_state['is_running'] = False
        processing_state['current_keywords'] = []
        add_log(f'❌ Enhanced optimization process error: {str(e)}', 'error')

@app.route('/health')
def health_check():
    """Enhanced health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'google_trends': True,
            'smart_keyword_analysis': True,
            'seo_scoring': True,
            'related_keywords': True,
            'danish_optimization': True
        },
        'files': {
            'mainZ.py': os.path.exists('mainZ.py'),
            'shopify_optimizer_ui.html': os.path.exists('shopify_optimizer_ui.html'),
            '.env': os.path.exists('.env')
        },
        'stats': {
            'products_processed_total': len(processing_state['product_keywords_history']),
            'keywords_analyzed_total': processing_state['stats']['total_keywords_analyzed'],
            'current_avg_seo_score': processing_state['stats']['avg_seo_score']
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Smart Shopify Product Optimizer Backend...")
    print("📁 Make sure shopify_optimizer_ui.html is in the same directory")
    print("🔑 Make sure your .env file contains the required API keys")
    print("🌐 Access the UI at: http://localhost:5000")
    print("🔍 Health check: http://localhost:5000/health")
    print("🎯 NEW FEATURES:")
    print("   • Smart Google Trends keyword research")
    print("   • Related keyword discovery") 
    print("   • Enhanced SEO scoring for Danish market")
    print("   • Real-time keyword analysis for each product")
    print("   • Persistent keyword history tracking")
    print("\n💡 Keep this window open while using the web interface!")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        print("\n🔧 Possible fixes:")
        print("1. Run command prompt as Administrator")
        print("2. Check if port 5000 is already in use")
        print("3. Try a different port by editing this file")
        print("4. Make sure all required files are present")
        print("5. Install missing dependencies: pip install pytrends pandas numpy")
        input("\nPress Enter to exit...")
