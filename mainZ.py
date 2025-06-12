#!/usr/bin/env python3
import os
import time
import re
import json
import logging
import requests
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from pytrends.request import TrendReq

load_dotenv()
STORE = os.getenv("SHOPIFY_STORE_NAME")
TOKEN = os.getenv("SHOPIFY_ADMIN_TOKEN")
API = os.getenv("OPENAI_API_KEY")
if not all([STORE, TOKEN, API]):
    raise SystemExit("❌ Missing credentials in .env file")
BASE = f"https://{STORE}/admin/api/2023-07"
HEADERS = {"Content-Type": "application/json", "X-Shopify-Access-Token": TOKEN}
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
client = OpenAI(api_key=API)

SUBCATEGORY_MAP = {
    # Hjem & Indretning
    "Alt Til Hjem & Indretning": "Hjem & Indretning",
    "Badeværelse": "Hjem & Indretning",
    "Soveværelse": "Hjem & Indretning",
    "Opbevaring & Organisering": "Hjem & Indretning",
    "Smart Home & Elektronik": "Hjem & Indretning",
    "Sæsonudsmykning & Fest": "Hjem & Indretning",
    "Jul & Højtidsudsmykning": "Hjem & Indretning",
    "Fest & Event Dekoration": "Hjem & Indretning",
    "Rengøring & Husholdning": "Hjem & Indretning",

    # Køkken & Spisestue
    "Alt Til Køkken & Spisestue": "Køkken & Spisestue",
    "Køkkenmaskiner & Elektronik": "Køkken & Spisestue",
    "Madlavning & Redskaber": "Køkken & Spisestue",
    "Bagning & Dekoration": "Køkken & Spisestue",
    "Kaffe & Teudstyr": "Køkken & Spisestue",
    "Service & Bestik": "Køkken & Spisestue",
    "Vin & Spiritus Tilbehør": "Køkken & Spisestue",
    "Bestik & Køkkenredskaber": "Køkken & Spisestue",

    # Kontor & Ergonomi
    "Alt Til Kontor & Ergonomi": "Kontor & Ergonomi",
    "Ergonomisk Udstyr": "Kontor & Ergonomi",
    "Opbevaring & Arkivering": "Kontor & Ergonomi",
    "Belysning & Lamper": "Kontor & Ergonomi",
    "Papirvarer & Kontorartikler": "Kontor & Ergonomi",

    # Baby & Børn
    "Alt Til Baby & Børn": "Baby & Børn",
    "Baby 0–2 år": "Baby & Børn",
    "Småbørn 3–6 år": "Baby & Børn",
    "Børn 7–12 år": "Baby & Børn",
    "Unge 13–18 år": "Baby & Børn",

    # Håndværk & DIY
    "Alt Til Håndværk & DIY": "Håndværk & DIY",
    "Smykkefremstilling": "Håndværk & DIY",
    "Syning & Broderi": "Håndværk & DIY",
    "Modelbygning": "Håndværk & DIY",
    "Papirkunst & Scrapbooking": "Håndværk & DIY",
    "Stearinlys & Sæbefremstilling": "Håndværk & DIY",
    "Resin & Epoxy Kunst": "Håndværk & DIY",
    "Keramik & Ler": "Håndværk & DIY",
    "Lasergravering & CNC": "Håndværk & DIY",
    "Bogbinding & Papirfremstilling": "Håndværk & DIY",

    # Gaming & E-Sport
    "Til Alt Gaming & E-Sport": "Gaming & E-Sport",
    "PC Gaming": "Gaming & E-Sport",
    "Konsol Gaming Tilbehør": "Gaming & E-Sport",
    "Streaming Udstyr": "Gaming & E-Sport",

    # Transport & Køretøjer
    "Alt Til Transport & Køretøjer": "Transport & Køretøjer",
    "Cykeludstyr": "Transport & Køretøjer",
    "Bilpleje & Vedligeholdelse": "Transport & Køretøjer",
    "Motorcykeludstyr": "Transport & Køretøjer",

    # Hus & Have
    "Alt Til Hus & Have": "Hus & Have",
    "Biavl & Havebrug": "Hus & Have",
    "Hydroponik & Indendørs Dyrkning": "Hus & Have",
    "Fuglehuse & Haveindretning": "Hus & Have",
    "Overlevelsesmad & Nødforsyninger": "Hus & Have",
    "Eksotiske Krybdyr & Terrarieudstyr": "Hus & Have",

    # Kæledyr
    "Alt Til Kæledyr": "Kæledyr",
    "Hunde": "Kæledyr",
    "Katte": "Kæledyr",

    # Livsstil & Velvære
    "Alt Til Livsstil & Velvære": "Livsstil & Velvære",
    "Fitness & Træning": "Livsstil & Velvære",
    "Personlig Pleje": "Livsstil & Velvære",
    "Skønhed & Kosmetik": "Livsstil & Velvære",
    "Sundhed & Velvære": "Livsstil & Velvære",

    # Teknologi & Fritid
    "Alt Til Teknologi & Fritid": "Teknologi & Fritid",
    "Hobby & Fritid": "Teknologi & Fritid",
    "Mobil- & Gadget tilbehør": "Teknologi & Fritid",
    "Rejse & Outdoor": "Teknologi & Fritid",

    # Årstiderne (keep as requested)
    "Sommer": "Årstiderne",
    "Vinter": "Årstiderne"
}

VENDORS = {
    "Hjem & Indretning": ["NordicLiving", "Hjemli", "Elm & Mälling"],
    "Køkken & Spisestue": ["NordicLiving", "Hjemli", "NordLiv"],
    "Kontor & Ergonomi": ["ErgoEdge", "Deskspire", "Workwell Co."],
    "Baby & Børn": ["TinyTrove", "CuddleClub", "MiniKram"],
    "Håndværk & DIY": ["MakerHaven", "Craftivo", "ToolMuse"],
    "Gaming & E-Sport": ["PixelForge", "CoreStriker", "Levelynx"],
    "Transport & Køretøjer": ["AutoFlux", "GearNova", "Mobelink"],
    "Hus & Have": ["Yardistry", "Greenstead", "HomeBloom"],
    "Kæledyr": ["Furora", "Paw & Whisker", "Tailish"],
    "Livsstil & Velvære": ["Vibe", "Bloomora", "Calmana"],
    "Teknologi & Fritid": ["Nexora", "TechLeap", "Bytecraft"],
    "Årstiderne": ["SeasonStyle", "Nordic Seasons", "TrendSeason"]
}

brand_memory = {}

# Available fields for updating
AVAILABLE_FIELDS = {
    'title': 'Product Title',
    'body_html': 'Product Description',
    'product_type': 'Product Type/Category',
    'vendor': 'Vendor/Brand',
    'handle': 'URL Handle',
    'seo_title': 'SEO Title (Meta Title)',
    'seo_description': 'SEO Description (Meta Description)'
}

def get_field_selection():
    """Interactive field selection menu"""
    print("\n" + "="*60)
    print("📝 SELECT FIELDS TO UPDATE")
    print("="*60)
    print("Available fields:")
    for i, (key, desc) in enumerate(AVAILABLE_FIELDS.items(), 1):
        print(f"  {i}. {desc}")
    
    print("\nOptions:")
    print("  a) Update ALL fields")
    print("  s) Select specific fields")
    print("  q) Quit")
    
    while True:
        choice = input("\nYour choice (a/s/q): ").lower().strip()
        
        if choice == 'q':
            print("Exiting...")
            exit(0)
        elif choice == 'a':
            return list(AVAILABLE_FIELDS.keys())
        elif choice == 's':
            return select_specific_fields()
        else:
            print("Invalid choice. Please enter 'a', 's', or 'q'.")

def select_specific_fields():
    """Allow user to select specific fields"""
    print("\n" + "-"*40)
    print("SELECT SPECIFIC FIELDS")
    print("-"*40)
    print("Enter field numbers separated by commas (e.g., 1,3,5)")
    print("Or enter field ranges (e.g., 1-3,5,7)")
    
    for i, (key, desc) in enumerate(AVAILABLE_FIELDS.items(), 1):
        print(f"  {i}. {desc}")
    
    while True:
        try:
            selection = input("\nEnter your selection: ").strip()
            if not selection:
                print("Please enter at least one field number.")
                continue
                
            selected_numbers = set()
            
            # Parse comma-separated values and ranges
            for part in selection.split(','):
                part = part.strip()
                if '-' in part:
                    # Handle ranges like "1-3"
                    start, end = map(int, part.split('-'))
                    selected_numbers.update(range(start, end + 1))
                else:
                    # Handle single numbers
                    selected_numbers.add(int(part))
            
            # Validate numbers
            field_keys = list(AVAILABLE_FIELDS.keys())
            valid_numbers = set(range(1, len(field_keys) + 1))
            
            if not selected_numbers.issubset(valid_numbers):
                invalid = selected_numbers - valid_numbers
                print(f"Invalid field numbers: {', '.join(map(str, invalid))}")
                print(f"Please use numbers 1-{len(field_keys)}")
                continue
            
            # Convert numbers to field keys
            selected_fields = [field_keys[i-1] for i in sorted(selected_numbers)]
            
            # Show confirmation
            print(f"\nSelected fields ({len(selected_fields)}):")
            for field in selected_fields:
                print(f"  ✓ {AVAILABLE_FIELDS[field]}")
            
            confirm = input("\nConfirm selection? (y/n): ").lower().strip()
            if confirm in ['y', 'yes']:
                return selected_fields
            elif confirm in ['n', 'no']:
                continue
            else:
                print("Please enter 'y' for yes or 'n' for no.")
                
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")
        except Exception as e:
            print(f"Error: {e}. Please try again.")

def rotate_brand(category):
    opts = VENDORS.get(category, [])
    if not opts:
        return None
    last = brand_memory.get(category)
    idx = (opts.index(last) + 1) % len(opts) if last in opts else 0
    choice = opts[idx]
    brand_memory[category] = choice
    return choice

def extract_keyword(title):
    base = re.split(r'[–\-|]', title)[0].strip()
    return re.sub(r'^(Ny|New|Original|Premium|Quality)\s+', '', base, flags=re.IGNORECASE)

def calculate_seo_score(keyword, interest, trend_direction, is_base=True):
    """Calculate SEO score for keyword based on multiple factors"""
    base_score = 50
    
    # Interest score (0-100) adds up to 30 points
    interest_points = min(30, (interest / 100) * 30)
    
    # Trend direction bonus/penalty
    trend_points = 0
    if trend_direction == "rising":
        trend_points = 15
    elif trend_direction == "stable":
        trend_points = 5
    elif trend_direction == "declining":
        trend_points = -10
    
    # Base keyword bonus
    base_bonus = 10 if is_base else 0
    
    # Keyword length penalty (very long keywords are less valuable)
    length_penalty = max(0, (len(keyword) - 30) * 0.5)
    
    total_score = base_score + interest_points + trend_points + base_bonus - length_penalty
    total_score = max(0, min(100, total_score))  # Clamp between 0-100
    
    # Assign grade
    if total_score >= 85:
        grade = "A+"
    elif total_score >= 75:
        grade = "A"
    elif total_score >= 65:
        grade = "B+"
    elif total_score >= 55:
        grade = "B"
    elif total_score >= 45:
        grade = "C+"
    elif total_score >= 35:
        grade = "C"
    else:
        grade = "D"
    
    return {
        "total_score": round(total_score, 1),
        "grade": grade,
        "interest_points": round(interest_points, 1),
        "trend_points": trend_points,
        "base_bonus": base_bonus
    }

def extract_smart_keywords_with_trends(title, region='DK', language='da-DK', max_related=3):
    """Faster keyword extraction with reduced complexity for better performance"""
    try:
        # Faster, more conservative settings
        pytrends = TrendReq(hl=language, tz=360, retries=1, backoff_factor=1, timeout=(5, 15))
        base_keyword = extract_keyword(title)
        keywords_data = []
        
        logging.info(f"🔍 Quick keyword analysis for: '{base_keyword}'")
        
        # Try main keyword with timeout
        main_data = get_keyword_trends_data_fast(pytrends, base_keyword, region, is_base=True)
        if main_data:
            keywords_data.append(main_data)
            logging.info(f"✅ Main keyword: {main_data['seo_score']['total_score']}/100")
        
        # Get fewer related keywords for speed
        if len(keywords_data) > 0:  # Only if main keyword worked
            related_keywords = get_related_keywords_fast(pytrends, base_keyword, max_related)
            for related in related_keywords[:2]:  # Maximum 2 related keywords
                related_data = get_keyword_trends_data_fast(pytrends, related, region, is_base=False)
                if related_data:
                    keywords_data.append(related_data)
                    logging.info(f"✅ Related: '{related}' ({related_data['seo_score']['total_score']}/100)")
        
        # Always add enhanced fallback keywords for consistent results
        fallback_keywords = generate_fallback_keywords(base_keyword)
        enhanced_fallbacks = generate_enhanced_seo_keywords(base_keyword)
        
        # Add up to 7 more keywords to reach 8 total
        all_fallbacks = fallback_keywords + enhanced_fallbacks
        target_count = 8  # Reduced from 12 to 8
        
        for fallback in all_fallbacks[:target_count]:
            if len(keywords_data) >= target_count:
                break
            if not any(kw['keyword'].lower() == fallback.lower() for kw in keywords_data):
                fallback_data = {
                    'keyword': fallback,
                    'interest': 35,  # Higher fallback score for better SEO
                    'peak_interest': 45,
                    'trend_direction': 'stable',
                    'is_base': False,
                    'seo_score': calculate_seo_score(fallback, 35, 'stable', False)
                }
                keywords_data.append(fallback_data)
        
        # Sort by SEO score and limit to 8 keywords
        keywords_data.sort(key=lambda x: x['seo_score']['total_score'], reverse=True)
        keywords_data = keywords_data[:8]
        
        trends_success = len([k for k in keywords_data if k['interest'] > 30])
        logging.info(f"🎯 Fast analysis complete: {len(keywords_data)} keywords ({trends_success} with trends)")
        return keywords_data
        
    except Exception as e:
        logging.warning(f"⚠️ Trends analysis failed, using enhanced fallbacks: {e}")
        
        # Fast fallback - no API calls
        base_keyword = extract_keyword(title)
        fallback_keywords = generate_fallback_keywords(base_keyword)
        enhanced_fallbacks = generate_enhanced_seo_keywords(base_keyword)
        
        fallback_data = []
        all_keywords = [base_keyword] + fallback_keywords + enhanced_fallbacks
        
        for i, keyword in enumerate(all_keywords[:8]):
            fallback_data.append({
                'keyword': keyword,
                'interest': 30,
                'peak_interest': 35,
                'trend_direction': 'stable',
                'is_base': i == 0,
                'seo_score': calculate_seo_score(keyword, 30, 'stable', i == 0)
            })
        
        logging.info(f"📝 Fast fallback: {len(fallback_data)} enhanced SEO keywords")
        return fallback_data

def get_keyword_trends_data_fast(pytrends, keyword, region, is_base=False):
    """Fast trends data with single attempt and short timeout"""
    try:
        pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo=region)
        interest_data = pytrends.interest_over_time()
        
        if not interest_data.empty and keyword in interest_data.columns:
            avg_interest = max(1, int(interest_data[keyword].mean()))
            peak_interest = max(avg_interest, int(interest_data[keyword].max()))
            
            # Simple trend calculation
            recent = interest_data[keyword].tail(4).mean()
            earlier = interest_data[keyword].head(4).mean()
            
            if recent > earlier * 1.1:
                trend_direction = "rising"
            elif recent < earlier * 0.9:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
            
            time.sleep(3)  # Reduced delay
            
            return {
                'keyword': keyword,
                'interest': avg_interest,
                'peak_interest': peak_interest,
                'trend_direction': trend_direction,
                'is_base': is_base,
                'seo_score': calculate_seo_score(keyword, avg_interest, trend_direction, is_base)
            }
        
    except Exception as e:
        logging.warning(f"⚠️ Fast trends failed for '{keyword}': {str(e)[:100]}")
    
    return None

def get_related_keywords_fast(pytrends, base_keyword, max_keywords=3):
    """Fast related keywords with reduced complexity"""
    try:
        time.sleep(5)  # Reduced delay
        related_queries = pytrends.related_queries()
        related_keywords = []
        
        if base_keyword in related_queries and related_queries[base_keyword]['top'] is not None:
            top_df = related_queries[base_keyword]['top']
            for _, row in top_df.head(max_keywords).iterrows():
                keyword = row['query'].lower().strip()
                if keyword != base_keyword.lower() and len(keyword) > 2:
                    related_keywords.append(keyword)
                    if len(related_keywords) >= max_keywords:
                        break
        
        logging.info(f"🔗 Fast related: {len(related_keywords)} keywords")
        return related_keywords
        
    except Exception as e:
        logging.warning(f"⚠️ Fast related keywords failed: {str(e)[:50]}")
        return []

def generate_fallback_keywords(base_keyword):
    """Generate smart fallback keywords when trends data is unavailable"""
    fallbacks = []
    base_lower = base_keyword.lower()
    
    # Add variations WITHOUT promotional words
    if "køkken" in base_lower:
        fallbacks.extend(["køkkenredskaber", "køkken tilbehør", "madlavning"])
    elif "bad" in base_lower or "badeværelse" in base_lower:
        fallbacks.extend(["badeværelse tilbehør", "bad design", "bathroom"])
    elif "have" in base_lower:
        fallbacks.extend(["have redskaber", "garden", "udendørs"])
    elif "børn" in base_lower or "baby" in base_lower:
        fallbacks.extend(["børn produkter", "baby udstyr", "kids"])
    elif "cykel" in base_lower:
        fallbacks.extend(["cykeludstyr", "cykel tilbehør", "cycling"])
    
    # Generic fallbacks WITHOUT promotional terms
    fallbacks.extend([
        base_keyword + " tilbehør",
        base_keyword + " redskaber",
        "professionel " + base_keyword
    ])
    
    return fallbacks[:5]

def generate_enhanced_seo_keywords(base_keyword):
    """Generate enhanced SEO keywords for better content optimization"""
    enhanced_keywords = []
    base_lower = base_keyword.lower()
    
    # Category-specific enhanced keywords
    if "køkken" in base_lower:
        enhanced_keywords.extend([
            "køkken design", "køkken kvalitet", "køkken funktionalitet",
            "køkken innovation", "køkken effektivitet", "køkken præcision"
        ])
    elif "cykel" in base_lower:
        enhanced_keywords.extend([
            "cykel performance", "cykel sikkerhed", "cykel komfort",
            "cykel holdbarhed", "cykel teknologi", "cykel kvalitet"
        ])
    elif "bad" in base_lower or "badeværelse" in base_lower:
        enhanced_keywords.extend([
            "bad design", "bad funktionalitet", "bad komfort",
            "bad kvalitet", "bad innovation", "bad løsninger"
        ])
    elif "have" in base_lower:
        enhanced_keywords.extend([
            "have pleje", "have design", "have funktionalitet",
            "have kvalitet", "have innovation", "have løsninger"
        ])
    elif "børn" in base_lower or "baby" in base_lower:
        enhanced_keywords.extend([
            "børn sikkerhed", "børn komfort", "børn kvalitet",
            "børn udvikling", "børn innovation", "børn løsninger"
        ])
    elif "kontor" in base_lower:
        enhanced_keywords.extend([
            "kontor produktivitet", "kontor ergonomi", "kontor komfort",
            "kontor kvalitet", "kontor innovation", "kontor løsninger"
        ])
    elif "gaming" in base_lower or "spil" in base_lower:
        enhanced_keywords.extend([
            "gaming performance", "gaming kvalitet", "gaming komfort",
            "gaming teknologi", "gaming innovation", "gaming oplevelse"
        ])
    
    # Universal enhanced keywords
    enhanced_keywords.extend([
        "premium " + base_keyword,
        "professionel " + base_keyword,
        "avanceret " + base_keyword,
        "høj kvalitet " + base_keyword,
        "moderne " + base_keyword,
        "innovativ " + base_keyword
    ])
    
    # Quality and feature keywords
    quality_keywords = [
        base_keyword + " kvalitet",
        base_keyword + " funktionalitet", 
        base_keyword + " design",
        base_keyword + " innovation",
        base_keyword + " løsninger",
        base_keyword + " teknologi"
    ]
    
    enhanced_keywords.extend(quality_keywords)
    
    # Remove duplicates and return
    return list(set(enhanced_keywords))[:10]

IMAGE_ANALYSIS_PROMPT = """
Analyze these product images and provide detailed information about:

Product Title: {keyword}
Image URLs:
{media}

Please analyze and describe:
1. Material composition
2. Shape and form factor
3. Colors visible
4. Size indicators
5. Functional features
6. Context of use
7. Number of items in set
8. Any variant options visible
9. Quality indicators

Provide a comprehensive description in Danish.
"""

def extract_product_attributes(product):
    """Extract all available product attributes for comprehensive analysis"""
    attributes = {
        'basic_info': {},
        'variants': [],
        'options': [],
        'metafields': {},
        'tags': [],
        'collections': []
    }
    
    # Basic product information
    attributes['basic_info'] = {
        'title': product.get('title', ''),
        'description': product.get('body_html', ''),
        'product_type': product.get('product_type', ''),
        'vendor': product.get('vendor', ''),
        'created_at': product.get('created_at', ''),
        'published_at': product.get('published_at', '')
    }
    
    # Extract variants with all their attributes
    variants = product.get('variants', [])
    for variant in variants:
        variant_info = {
            'title': variant.get('title', ''),
            'price': variant.get('price', ''),
            'compare_at_price': variant.get('compare_at_price', ''),
            'sku': variant.get('sku', ''),
            'barcode': variant.get('barcode', ''),
            'weight': variant.get('weight', ''),
            'weight_unit': variant.get('weight_unit', ''),
            'inventory_quantity': variant.get('inventory_quantity', 0),
            'option1': variant.get('option1', ''),  # Often Color
            'option2': variant.get('option2', ''),  # Often Size
            'option3': variant.get('option3', ''),  # Often Material/Style
        }
        attributes['variants'].append(variant_info)
    
    # Extract product options (Color, Size, Material, etc.)
    options = product.get('options', [])
    for option in options:
        option_info = {
            'name': option.get('name', ''),
            'values': option.get('values', [])
        }
        attributes['options'].append(option_info)
    
    # Extract tags
    tags = product.get('tags', '')
    if tags:
        attributes['tags'] = [tag.strip() for tag in tags.split(',')]
    
    # Try to extract metafields if available
    metafields = product.get('metafields', [])
    for metafield in metafields:
        key = metafield.get('key', '')
        value = metafield.get('value', '')
        namespace = metafield.get('namespace', '')
        if key and value:
            attributes['metafields'][f"{namespace}.{key}"] = value
    
    return attributes

def generate_product_attributes_text(attributes):
    """Generate comprehensive product attributes text for AI analysis"""
    attr_text = "=== KOMPLET PRODUKT INFORMATION ===\n\n"
    
    # Basic info
    basic = attributes['basic_info']
    attr_text += f"📋 GRUNDLÆGGENDE:\n"
    attr_text += f"- Titel: {basic['title']}\n"
    attr_text += f"- Produkttype: {basic['product_type']}\n"
    attr_text += f"- Leverandør: {basic['vendor']}\n"
    if basic['description']:
        current_desc = basic['description'][:200].replace('<', '').replace('>', '')
        attr_text += f"- Nuværende beskrivelse: {current_desc}...\n"
            
        attr_text += "\n"
    
    # Product options
    options = attributes['options']
    if options:
        attr_text += f"🔧 PRODUKT MULIGHEDER:\n"
        for option in options:
            name = option['name']
            values = option['values']
            if values:
                attr_text += f"- {name}: {', '.join(values)}\n"
        attr_text += "\n"
    
    # Tags analysis
    tags = attributes['tags']
    if tags:
        relevant_tags = [tag for tag in tags if tag.lower() not in ['needs_update', 'updated_gpt']]
        if relevant_tags:
            attr_text += f"🏷️ RELEVANTE TAGS:\n"
            attr_text += f"- {', '.join(relevant_tags)}\n\n"
    
    # Metafields
    metafields = attributes['metafields']
    if metafields:
        attr_text += f"📊 EKSTRA INFORMATION:\n"
        for key, value in metafields.items():
            attr_text += f"- {key}: {value}\n"
        attr_text += "\n"

    # Variants analysis
    variants = attributes['variants']
    if variants:
        attr_text += f"🎨 VARIANTER OG SPECIFIKATIONER ({len(variants)} stk):\n"

        # Collect all unique attributes
        colors = set()
        sizes = set()
        materials = set()
        weights = []
        prices = []

        for variant in variants:
            if variant['option1'] and variant['option1'] != 'Default Title':
                colors.add(variant['option1'])
            if variant['option2'] and variant['option2'] != 'Default Title':
                sizes.add(variant['option2'])
            if variant['option3'] and variant['option3'] != 'Default Title':
                materials.add(variant['option3'])

            if variant['weight']:
                try:
                    weight_val = float(variant['weight'])
                    unit = variant['weight_unit'] or 'g'
                    weights.append(f"{weight_val}{unit}")
                except:
                    pass

            if variant['price']:
                try:
                    prices.append(float(variant['price']))
                except:
                    pass

        if colors:
            attr_text += f"- Farver: {', '.join(sorted(colors))}\n"
        if sizes:
            attr_text += f"- Størrelser: {', '.join(sorted(sizes))}\n"
        if materials:
            attr_text += f"- Materialer: {', '.join(sorted(materials))}\n"
        if weights:
            unique_weights = list(set(weights))
            attr_text += f"- Vægt: {', '.join(unique_weights)}\n"
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            if min_price == max_price:
                attr_text += f"- Pris: {min_price} DKK\n"
            else:
                attr_text += f"- Prisområde: {min_price}-{max_price} DKK\n"

    return attr_text

COMPREHENSIVE_CONTENT_GENERATION_PROMPT = """
Du er en professionel dansk Shopify SEO specialist med ekspertise i Google Trends og keyword-optimering.

=== SMART KEYWORD DATA ===
{keywords_analysis}

=== PRODUKT INFORMATION ===
{product_attributes}

=== BILLEDE ANALYSE ===
{image_analysis}

=== KATEGORI & BRAND INFO ===
Kategori mapping: {subcategories}
Brand options: {vendors}

=== BRAND KONSISTENS ===
KRITISK: Brug SAMME brand/vendor i ALLE felter:
- Vælg ét brand fra vendor options til kategorien
- Brug dette brand i specifikationer tabel
- Brug IKKE andre brand navne i beskrivelser
- Hold brand konsistent gennem hele produktet

=== SEO STRATEGI ===
VIGTIGT: Brug ALL tilgængelige data til at optimere indhold:

1. PRIORITER højeste SEO score keywords (A+ og A grade) først i titles
2. INKLUDER trending keywords (rising direction) i beskrivelser  
3. BRUG produkt attributter (farver, størrelser, materialer, vægt) naturligt
4. INTEGRER variant information i features og specifikationer
5. UNDGÅ promotional ord som "køb", "online", "bestil" i titles
6. BRUG tags som inspiration til features og benefits

=== PRODUKT DATA INTEGRATION ===
Brug tilgængelige produkt data smart:
- FARVER: Inkluder i titel og beskrivelse hvis relevant
- STØRRELSER/DIMENSIONER: Nævn i specifikationer og features
- MATERIALER: Fremhæv i kvalitetsbeskrivelse
- VÆGT/KAPACITET: Inkluder i specifikationer
- VARIANT MULIGHEDER: Beskriv i features
- TAGS: Brug som inspiration til benefits

=== OUTPUT FORMAT ===
Generer et JSON objekt med nøgler:
- product_type
- vendor  
- title
- body_html
- seo_title
- seo_description
- handle

=== CONTENT KRAV ===

**Title**: 
- Start med højeste scoring keyword
- Inkluder primære attributter (farve/størrelse hvis relevant)
- BESKRIVENDE og forklarende (ikke salgs-orienteret)
- INGEN promotional ord: "køb", "online", "bestil", "shop"
- 100-120 karakterer
- Ingen brandnavn

**body_html struktur (minimum 600 ord)**:
1. <h1><strong><em>{{title}}</em></strong></h1>
2. Tre SEO-optimerede afsnit med <h2> og <p> - integrer produkt attributter naturligt
3. <ul> med 4-6 vigtigste features (brug variant data og attributter)
4. <h2>Specifikationer</h2> med <table> (inkluder ALL relevante data: brand, farver, størrelser, vægt, materialer)
5. Afsluttende <h2> afsnit med call-to-action

**seo_title**: 
- Brug absolut bedste keywords først
- Inkluder primære attributter
- BESKRIVENDE ikke promotional
- 70-80 karakterer
- Ingen brandnavn

**seo_description**:
- Inkluder top keywords + vigtigste attributter
- 150-170 karakterer  
- Ingen brandnavn
- Compelling og action-oriented

Alt indhold på dansk. Ingen emojis. Returner kun valid JSON.

=== EKSEMPEL PÅ ATTRIBUTE INTEGRATION ===
Hvis produkt har:
- Farver: Blå, Grøn, Sort
- Størrelse: 15cm diameter  
- Materiale: Plastik og Metal
- Vægt: 250g

Title: "Professionelle Cykeludstyr i Plastik og Metal - 15cm Kædeolierer til Cykel i Blå, Grøn og Sort"

Specifikationer tabel skal inkludere:
| Specifikation | Værdi |
|---------------|--------|
| Brand | [Selected Vendor] |
| Farver | Blå, Grøn, Sort |
| Størrelse | 15cm diameter |
| Materiale | Plastik og Metal |
| Vægt | 250g |

=== BRAND KONSISTENS EKSEMPEL ===
Hvis vendor er "AutoFlux":
- Specifikationer tabel: Brand: AutoFlux
- IKKE brug "GearNova" eller andre brands i beskrivelsen
- Hold alle brand referencer til valgte vendor
"""

def generate_keywords_analysis_text(keywords_data):
    """Generate detailed analysis text for the AI prompt"""
    if not keywords_data:
        return "Ingen keyword data tilgængelig."
    
    analysis = "=== KEYWORD ANALYSE RESULTATER ===\n\n"
    
    # Summary stats
    total_keywords = len(keywords_data)
    avg_score = sum(k['seo_score']['total_score'] for k in keywords_data) / total_keywords
    best_keyword = max(keywords_data, key=lambda x: x['seo_score']['total_score'])
    rising_keywords = [k for k in keywords_data if k['trend_direction'] == 'rising']
    
    analysis += f"📊 SAMMENFATNING:\n"
    analysis += f"- Total keywords: {total_keywords}\n"
    analysis += f"- Gennemsnitlig SEO score: {avg_score:.1f}/100\n"
    analysis += f"- Bedste keyword: '{best_keyword['keyword']}' ({best_keyword['seo_score']['grade']} grade, {best_keyword['seo_score']['total_score']} score)\n"
    analysis += f"- Trending keywords (rising): {len(rising_keywords)}\n\n"
    
    # Detailed keyword breakdown
    analysis += "🎯 KEYWORD DETALJER (sorteret efter SEO score):\n\n"
    
    for i, kw in enumerate(keywords_data, 1):
        seo = kw['seo_score']
        trend_emoji = "📈" if kw['trend_direction'] == 'rising' else "📊" if kw['trend_direction'] == 'stable' else "📉"
        type_label = "[BASE]" if kw['is_base'] else "[RELATED]"
        
        analysis += f"{i}. {type_label} '{kw['keyword']}'\n"
        analysis += f"   SEO Score: {seo['total_score']}/100 (Grade: {seo['grade']})\n"
        analysis += f"   Interest: {kw['interest']}/100 | Peak: {kw['peak_interest']}\n"
        analysis += f"   Trend: {trend_emoji} {kw['trend_direction']}\n"
        analysis += f"   Score breakdown: Interest({seo['interest_points']}) + Trend({seo['trend_points']}) + Base({seo['base_bonus']})\n\n"
    
    # Strategic recommendations
    analysis += "💡 SEO ANBEFALINGER:\n"
    top_3 = keywords_data[:3]
    top_keywords_text = ', '.join([f"'{k['keyword']}' ({k['seo_score']['grade']})" for k in top_3])
    analysis += f"- Prioriter disse keywords i title: {top_keywords_text}\n"
    
    if rising_keywords:
        analysis += f"- Trending keywords til beskrivelse: {', '.join([k['keyword'] for k in rising_keywords[:2]])}\n"
    
    high_value = [k for k in keywords_data if k['seo_score']['total_score'] >= 70]
    if high_value:
        analysis += f"- High-value keywords (70+ score): {len(high_value)} stk\n"
    
    return analysis

def safe_json(text):
    try:
        clean = re.sub(r'```json\s*', '', text)
        clean = re.sub(r'```\s*', '', clean)
        m = re.search(r'\{.*?\}', clean, re.DOTALL)
        if m:
            return json.loads(m.group())
    except:
        pass
    return {}

def create_handle(keyword):
    h = keyword.lower()
    h = h.replace('æ','ae').replace('ø','oe').replace('å','aa')
    h = re.sub(r'[^\w\s-]', '', h)
    h = re.sub(r'\s+', '-', h)
    return h.strip('-')[:80]

def fetch_products(limit=None):
    products, since = [], 0
    while True:
        r = requests.get(f"{BASE}/products.json", headers=HEADERS, params={'limit':250,'since_id':since})
        r.raise_for_status()
        batch = r.json().get('products', [])
        if not batch: break
        products += [p for p in batch if 'needs_update' in p.get('tags','').lower()]
        since = batch[-1]['id']
        if limit and len(products) >= limit: return products[:limit]
        time.sleep(0.3)
    return products

def analyze_images(keyword, urls):
    text_prompt = IMAGE_ANALYSIS_PROMPT.format(keyword=keyword, media=urls)
    messages = [{'role':'user','content': text_prompt}]
    if urls:
        for u in urls.split("\n")[:3]:
            if u.strip(): messages.append({'role':'user','content': u.strip()})
    try:
        resp = client.chat.completions.create(model='gpt-4o', messages=messages, max_tokens=500)
        return resp.choices[0].message.content
    except:
        try:
            resp = client.chat.completions.create(model='gpt-4o', messages=[{'role':'user','content': text_prompt}], max_tokens=500)
            return resp.choices[0].message.content
        except:
            return f"Billedanalyse ikke tilgængelig for {keyword}."

def generate_smart_content(keyword, analysis, use_trends=True, region='DK', language='da-DK', product_data=None):
    """Enhanced content generation with detailed keyword analysis and product attributes"""
    
    # Get smart keywords with trends data
    if use_trends:
        keywords_data = extract_smart_keywords_with_trends(keyword, region, language)
        logging.info(f"📈 Smart keywords analysis: {len(keywords_data)} keywords, avg score: {sum(k['seo_score']['total_score'] for k in keywords_data)/len(keywords_data):.1f}")
        
        # Log the keywords being used (for verification)
        for kw in keywords_data[:3]:
            logging.info(f"🎯 Using keyword: '{kw['keyword']}' (Score: {kw['seo_score']['total_score']}, Grade: {kw['seo_score']['grade']})")
    else:
        keywords_data = [{
            'keyword': keyword, 
            'interest': 20, 
            'peak_interest': 20, 
            'trend_direction': 'unknown', 
            'is_base': True,
            'seo_score': calculate_seo_score(keyword, 20, 'unknown', True)
        }]
        logging.info("⚠️ Using basic keyword extraction (trends disabled)")
    
    # Generate detailed analysis for the prompt
    keywords_analysis = generate_keywords_analysis_text(keywords_data)
    
    # Extract and format product attributes
    if product_data:
        product_attributes_data = extract_product_attributes(product_data)
        product_attributes_text = generate_product_attributes_text(product_attributes_data)
        logging.info(f"📦 Product attributes extracted: {len(product_attributes_data['variants'])} variants, {len(product_attributes_data['options'])} options, {len(product_attributes_data['tags'])} tags")
    else:
        product_attributes_text = "Ingen ekstra produkt attributter tilgængelige."
        logging.warning("⚠️ No product data provided for attribute extraction")
    
    # Enhanced prompt with comprehensive product data
    prompt = COMPREHENSIVE_CONTENT_GENERATION_PROMPT.format(
        keywords_analysis=keywords_analysis,
        product_attributes=product_attributes_text,
        image_analysis=analysis,
        subcategories=json.dumps(SUBCATEGORY_MAP, ensure_ascii=False),
        vendors=json.dumps(VENDORS, ensure_ascii=False)
    )
    
    # Log what we're sending to ChatGPT (for verification)
    logging.info(f"🤖 Sending to ChatGPT: {len(keywords_data)} keywords (up from 5), best: '{keywords_data[0]['keyword']}' ({keywords_data[0]['seo_score']['grade']})")
    logging.info(f"📸 Image analysis: {'✅ Included' if analysis and 'ikke tilgængelig' not in analysis else '❌ Failed'}")
    logging.info(f"📦 Product attributes: {'✅ Comprehensive data' if product_data else '❌ Basic only'}")
    logging.info(f"🎯 SEO keyword coverage: A+ grades: {len([k for k in keywords_data if k['seo_score']['grade'] == 'A+'])}, A grades: {len([k for k in keywords_data if k['seo_score']['grade'] == 'A'])}")
    
    try:
        resp = client.chat.completions.create(
            model='gpt-4o', 
            messages=[{'role':'user','content':prompt}], 
            max_tokens=2500, 
            temperature=0.7
        )
        
        result = safe_json(resp.choices[0].message.content)
        
        if result:
            # Verify keywords are being used in the generated content
            generated_title = result.get('title', '').lower()
            generated_desc = result.get('body_html', '').lower()
            
            keywords_found_in_title = sum(1 for kw in keywords_data if kw['keyword'].lower() in generated_title)
            keywords_found_in_desc = sum(1 for kw in keywords_data if kw['keyword'].lower() in generated_desc)
            
            logging.info(f"✅ Content generated! Keywords in title: {keywords_found_in_title}/{len(keywords_data)}, in description: {keywords_found_in_desc}/{len(keywords_data)}")
            
            # Store keyword data in result for verification
            result['_keyword_verification'] = {
                'keywords_used': keywords_data,
                'keywords_in_title': keywords_found_in_title,
                'keywords_in_description': keywords_found_in_desc,
                'best_keyword_used': keywords_data[0]['keyword'].lower() in generated_title
            }
        
        return result
        
    except Exception as e:
        logging.error(f"❌ ChatGPT content generation failed: {e}")
        return {}

def update_product(prod, data, selected_fields):
    """Update product with only the selected fields"""
    pid = prod['id']
    kw = extract_keyword(prod.get('title',''))
    
    # Log keyword verification if available
    if '_keyword_verification' in data:
        verification = data['_keyword_verification']
        logging.info(f"🔍 Keyword verification for product {pid}:")
        logging.info(f"   Best keyword in title: {'✅' if verification['best_keyword_used'] else '❌'}")
        logging.info(f"   Total keywords in content: {verification['keywords_in_title']} title + {verification['keywords_in_description']} description")
    
    # Prepare payload with only selected fields
    payload = {'product': {'id': pid}}
    
    # Get the vendor that will be used for brand consistency
    selected_vendor = None
    if 'vendor' in selected_fields:
        cat = data.get('product_type', '')
        main = SUBCATEGORY_MAP.get(cat, cat)
        selected_vendor = rotate_brand(main)
        if selected_vendor:
            payload['product']['vendor'] = selected_vendor
            logging.info(f"🏷️ Selected vendor: {selected_vendor} for category: {main}")
    
    # Process each selected field
    if 'title' in selected_fields and data.get('title'):
        payload['product']['title'] = data['title'][:120]
    
    if 'product_type' in selected_fields and data.get('product_type'):
        payload['product']['product_type'] = data['product_type']
    
    if 'handle' in selected_fields:
        handle = data.get('handle', create_handle(kw))
        payload['product']['handle'] = handle
    
    if 'body_html' in selected_fields and data.get('body_html'):
        body = data['body_html']
        
        # CRITICAL: Replace ALL brand names with the selected vendor for consistency
        if selected_vendor:
            # Replace any brand names from all vendor categories with selected vendor
            for category_vendors in VENDORS.values():
                for brand in category_vendors:
                    if brand != selected_vendor:
                        body = body.replace(brand, selected_vendor)
            logging.info(f"🔄 Brand consistency: Replaced all brands with {selected_vendor}")
        
        # Replace placeholders
        final_handle = payload['product'].get('handle', create_handle(kw))
        final_title = payload['product'].get('title', data.get('title', kw))
        body = body.replace('{handle}', final_handle).replace('{title}', final_title)
        payload['product']['body_html'] = body
    
    # Handle SEO fields (metafields)
    if 'seo_title' in selected_fields and data.get('seo_title'):
        payload['product']['metafields_global_title_tag'] = data['seo_title'][:60]
    
    if 'seo_description' in selected_fields and data.get('seo_description'):
        payload['product']['metafields_global_description_tag'] = data['seo_description'][:160]
    
    # Always update tags to remove needs_update and add updated_gpt
    tags = [t.strip() for t in prod.get('tags','').split(',') if t.strip().lower()!='needs_update'] + ['updated_gpt']
    payload['product']['tags'] = ','.join(tags)
    
    # Log which fields are being updated
    updated_fields = [AVAILABLE_FIELDS[field] for field in selected_fields if field in payload['product'] or field.startswith('seo_')]
    logging.info(f"Updating fields: {', '.join(updated_fields)}")
    
    r = requests.put(f"{BASE}/products/{pid}.json", headers=HEADERS, json=payload)
    r.raise_for_status()
    return True

def optimize_product(prod, selected_fields, use_trends=True, region='DK', language='da-DK'):
    kw = extract_keyword(prod.get('title',''))
    imgs = '\n'.join([i['src'] for i in prod.get('images',[])[:3]])
    analysis = analyze_images(kw, imgs)
    
    # Pass the full product data for comprehensive attribute extraction
    content = generate_smart_content(kw, analysis, use_trends, region, language, prod)
    return content and update_product(prod, content, selected_fields)

def main():
    p = argparse.ArgumentParser(description='Smart Shopify Product Optimizer with Google Trends & SEO Ranking')
    p.add_argument('--limit', type=int, help='Limit number of products to process')
    p.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    p.add_argument('--fields', nargs='+', choices=list(AVAILABLE_FIELDS.keys()), 
                   help='Specify fields to update directly (skip interactive selection)')
    p.add_argument('--skip-trends', action='store_true', help='Skip Google Trends analysis')
    p.add_argument('--region', default='DK', help='Google Trends region (default: DK)')
    p.add_argument('--language', default='da-DK', help='Language for trends (default: da-DK)')
    p.add_argument('--test-keyword', help='Test keyword analysis without processing products')
    p.add_argument('--trends-delay', type=int, default=15, help='Delay between trends requests (default: 15 seconds)')
    args = p.parse_args()
    
    if args.verbose: 
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Test keyword analysis feature
    if args.test_keyword:
        print(f"\n🔍 Testing keyword analysis for: '{args.test_keyword}'")
        print(f"⏱️ Using {args.trends_delay}s delays between requests")
        keywords_data = extract_smart_keywords_with_trends(args.test_keyword, args.region, args.language)
        
        print(f"\n📊 Results:")
        print(f"Total keywords found: {len(keywords_data)}")
        trends_count = len([k for k in keywords_data if k['interest'] > 25])
        print(f"With real trends data: {trends_count}/{len(keywords_data)}")
        
        for i, kw in enumerate(keywords_data, 1):
            trend_emoji = "📈" if kw['trend_direction'] == 'rising' else "📊" if kw['trend_direction'] == 'stable' else "📉"
            type_label = "BASE" if kw['is_base'] else "RELATED"
            print(f"{i}. [{type_label}] '{kw['keyword']}'")
            print(f"   Score: {kw['seo_score']['total_score']}/100 (Grade: {kw['seo_score']['grade']})")
            print(f"   Interest: {kw['interest']}/100 | Trend: {trend_emoji} {kw['trend_direction']}")
        
        print(f"\n✅ Test complete!")
        if trends_count < len(keywords_data) // 2:
            print(f"💡 Rate limiting detected. Enhanced SEO keywords were used as fallbacks.")
            print(f"💡 Consider using --trends-delay 20 for better success rate with trends.")
        return
    
    # Get field selection
    if args.fields:
        selected_fields = args.fields
        print(f"Using command-line field selection: {', '.join([AVAILABLE_FIELDS[f] for f in selected_fields])}")
    else:
        selected_fields = get_field_selection()
    
    if not selected_fields:
        print("No fields selected. Exiting.")
        return
    
    use_trends = not args.skip_trends
    print(f"\n🔄 Will update these fields: {', '.join([AVAILABLE_FIELDS[f] for f in selected_fields])}")
    print(f"📈 Smart Google Trends: {'✅ Enabled' if use_trends else '❌ Disabled'}")
    if use_trends:
        print(f"🌍 Region: {args.region} | Language: {args.language}")
        print(f"⏱️ Rate limiting: {args.trends_delay}s delays between requests")
        print(f"🎯 Features: SEO scoring, related keywords, trend analysis, enhanced fallbacks")
    
    logging.info("🔍 Fetching needs_update products...")
    prods = fetch_products(limit=args.limit)
    
    if not prods: 
        logging.info("No products to process.")
        return
    
    print(f"\n📦 Found {len(prods)} products to process")
    
    # Final confirmation
    if not args.fields:  # Only ask for confirmation in interactive mode
        confirm = input(f"Continue with processing {len(prods)} products? (y/n): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled.")
            return
    
    cnt = 0
    trends_success = 0
    keyword_verification_stats = {'total_products': 0, 'keywords_in_titles': 0, 'keywords_in_descriptions': 0}
    
    for idx, pr in enumerate(prods, 1):
        logging.info(f"Processing {idx}/{len(prods)}: {pr['id']} - {pr.get('title', 'No title')[:50]}...")
        try:
            if optimize_product(pr, selected_fields, use_trends, args.region, args.language): 
                cnt += 1
                if use_trends:
                    trends_success += 1
                logging.info(f"✅ Successfully updated product {pr['id']}")
            else:
                logging.warning(f"❌ Failed to update product {pr['id']}")
        except Exception as e:
            logging.error(f"❌ Error processing product {pr['id']}: {e}")
        
        # Enhanced delay between products when using trends
        if use_trends and idx < len(prods):
            delay = args.trends_delay
            logging.info(f"⏳ Waiting {delay}s before next product to respect rate limits...")
            time.sleep(delay)
        else:
            time.sleep(2)
    
    print(f"\n🎉 Processing complete!")
    print(f"✅ Successfully updated: {cnt}/{len(prods)} products")
    print(f"📊 Updated fields: {', '.join([AVAILABLE_FIELDS[f] for f in selected_fields])}")
    if use_trends:
        print(f"📈 Google Trends success rate: {trends_success}/{cnt} ({round(trends_success/cnt*100) if cnt > 0 else 0}%)")
        print(f"🎯 Smart SEO features: keyword scoring, trend analysis, related keywords discovery, enhanced fallbacks")

if __name__=='__main__':
    main()
