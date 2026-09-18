import json
import logging
import urllib.request
import urllib.error
from config import Config

logger = logging.getLogger(__name__)

def limit_to_max_words(text, max_words=15):
    """Ensures text strictly has at most max_words words."""
    if not text:
        return ""
    words = str(text).strip().split()
    if len(words) <= max_words:
        return str(text).strip()
    return " ".join(words[:max_words]).rstrip(",;:-") + "."


def generate_review_suggestions(
    employee_name, 
    designation="", 
    company_name="", 
    bio="", 
    tone="friendly", 
    custom_topic="",
    star_rating=5,
    categories=None
):
    """
    Generates 3 context-aware Google Review suggestions using Gemini AI API
    tailored to specific star ratings (1 to 5) and business categories/services.
    STRICT CONSTRAINT: Maximum 15 words per review suggestion.
    Falls back gracefully to intelligent domain-tailored templates if API is unreachable.
    """
    api_key = Config.GEMINI_API_KEY
    model = Config.GEMINI_MODEL or 'gemini-3.7-flash'
    
    employee_name = employee_name or 'the team member'
    designation = designation or 'Professional'
    company_name = company_name or 'the company'
    
    # Sanitize star rating
    try:
        star_rating = max(1, min(5, int(star_rating)))
    except (TypeError, ValueError):
        star_rating = 5

    # Sanitize categories list
    cat_list = []
    if isinstance(categories, list):
        cat_list = [c.strip() for c in categories if isinstance(c, str) and c.strip()]
    elif isinstance(categories, str) and categories.strip():
        cat_list = [c.strip() for c in categories.split(',') if c.strip()]

    # Map tone instructions
    tone_descriptions = {
        'friendly': 'warm, appreciative, conversational, and enthusiastic',
        'detailed': 'highlighting professionalism, expertise, and specific quality',
        'quick': 'short, punchy, direct, highly positive',
        'recommended': 'strongly endorsing and recommending to everyone',
        'supportive': 'focused on responsiveness, polite communication, and helpful guidance'
    }
    tone_guide = tone_descriptions.get(tone, tone_descriptions['friendly'])
    
    # Map star rating sentiment guide
    star_sentiments = {
        5: "5-star rating (Outstanding excellence, highest praise, 100% recommended)",
        4: "4-star rating (Very good experience, satisfied with overall service)",
        3: "3-star rating (Moderate / average experience, polite constructive feedback)",
        2: "2-star rating (Below average experience, fair but pointing out specific delays politely)",
        1: "1-star rating (Critical review highlighting shortcomings politely)"
    }
    rating_guide = star_sentiments.get(star_rating, star_sentiments[5])

    category_instruction = ""
    if cat_list:
        clean_cats = ", ".join(cat_list)
        category_instruction = f" Specifically focus on and mention these business services/categories: '{clean_cats}'."

    topic_instruction = f" Mention aspects related to: '{custom_topic}'." if custom_topic else ""

    prompt = (
        f"You are an assistant creating authentic, punchy Google Review suggestions for a customer to post on Google My Business (GMB) about "
        f"{employee_name}, who works as a {designation} at {company_name}.\n"
        f"Target Rating: {rating_guide}\n"
        f"Context / Bio: {bio or 'A dedicated professional delivering top-tier service.'}\n"
        f"Tone: {tone_guide}.{category_instruction}{topic_instruction}\n\n"
        f"CRITICAL CONSTRAINT: Each 'review' MUST be strictly MAXIMUM 15 WORDS (short, punchy, concise, under 15 words).\n\n"
        f"Requirements:\n"
        f"1. Generate exactly 3 distinct, realistic, high-quality review suggestions matching the {star_rating}-star rating.\n"
        f"2. Adapt the vocabulary and context precisely to their business field and the selected categories.\n"
        f"3. Do NOT use overly robotic or marketing-heavy jargon. Make it sound like a real customer.\n"
        f"4. Return STRICTLY a JSON array of 3 objects, each with:\n"
        f"   - 'title': Short headline (2 to 5 words)\n"
        f"   - 'review': Punchy review text (STRICTLY MAXIMUM 15 WORDS)\n"
        f"   - 'rating': Integer {star_rating}\n"
        f"   - 'tags': Array of 2-3 short highlight tags (e.g., ['{cat_list[0] if cat_list else 'Great Service'}', '{star_rating} Stars'])\n"
    )

    if api_key and not api_key.startswith('your_'):
        models_to_try = [model, 'gemini-3.7-flash', 'gemini-3.8-flash', 'gemini-3.5-flash']
        # Remove duplicates while preserving order
        seen = set()
        unique_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

        for mod in unique_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=12) as response:
                    if response.status == 200:
                        raw_data = response.read().decode('utf-8')
                        resp_json = json.loads(raw_data)
                        text_content = resp_json['candidates'][0]['content']['parts'][0]['text']
                        parsed_reviews = json.loads(text_content)
                        if isinstance(parsed_reviews, list) and len(parsed_reviews) > 0:
                            sanitized = []
                            for item in parsed_reviews[:3]:
                                raw_review = str(item.get("review", "")).strip()
                                trimmed_review = limit_to_max_words(raw_review, max_words=15)
                                sanitized.append({
                                    "title": str(item.get("title", "Recommended Experience")).strip(),
                                    "review": trimmed_review,
                                    "rating": star_rating,
                                    "tags": item.get("tags", [f"{star_rating} Stars"]) if isinstance(item.get("tags"), list) else [f"{star_rating} Stars"]
                                })
                            return {
                                "success": True,
                                "source": "gemini_ai",
                                "model": mod,
                                "star_rating": star_rating,
                                "reviews": sanitized
                            }
            except Exception as e:
                logger.warning("Gemini AI API call failed for model %s: %s", mod, e)

    # Fallback to intelligent dynamic templates
    return {
        "success": True,
        "source": "smart_fallback",
        "star_rating": star_rating,
        "reviews": generate_fallback_reviews(employee_name, designation, company_name, custom_topic, star_rating, cat_list)
    }


def generate_fallback_reviews(name, designation, company, topic="", star_rating=5, categories=None):
    """
    Provides rich, domain and star-aware fallback reviews in case of API unavailability.
    All fallback reviews are strictly constrained to maximum 15 words.
    """
    cats = categories or []
    cat_str = f" for {', '.join(cats)}" if cats else ""
    desig_lower = (designation or "").lower()
    
    # Build domain keyword text
    is_clothing = any(k in desig_lower for k in ['menswear', 'clothing', 'fashion', 'tailor', 'suit', 'fabric', 'retail', 'apparel'])
    is_doctor = any(k in desig_lower for k in ['doctor', 'dr', 'physician', 'surgeon', 'cardiologist', 'dentist', 'clinic', 'hospital', 'nurse'])
    is_realestate = any(k in desig_lower for k in ['real estate', 'realtor', 'property', 'broker', 'housing', 'builder'])
    
    tag_prefix = cats[0] if cats else "Top Service"

    raw_list = []
    if star_rating >= 4:
        if is_clothing:
            raw_list = [
                {
                    "title": f"Outstanding quality & perfect fitting{cat_str}",
                    "review": f"Incredible experience shopping with {name} at {company}{cat_str}! Top quality and perfect fitting.",
                    "rating": star_rating,
                    "tags": [tag_prefix, f"{star_rating} Stars", "Verified Buyer"]
                },
                {
                    "title": "Superb collection and great customer service",
                    "review": f"{name} was super helpful and knowledgeable about current trends{cat_str}. Found exactly what I needed!",
                    "rating": star_rating,
                    "tags": ["Great Collection", "Helpful Staff", "5 Stars" if star_rating == 5 else "4 Stars"]
                },
                {
                    "title": "Seamless tailoring and fast delivery",
                    "review": f"Fast turnaround and flawless craftsmanship at {company}. {name} delivered outstanding fitting results!",
                    "rating": star_rating,
                    "tags": ["Flawless Fitting", "Fast Delivery", "Recommended"]
                }
            ]
        elif is_doctor:
            raw_list = [
                {
                    "title": "Exceptional care and true professionalism",
                    "review": f"Outstanding care by {name} at {company}{cat_str}. Extremely compassionate, attentive, and highly skilled!",
                    "rating": star_rating,
                    "tags": ["Compassionate Care", "Highly Skilled", "Recommended"]
                },
                {
                    "title": "Very attentive and knowledgeable doctor",
                    "review": f"{name} listened patiently and provided clear, effective medical advice at {company}. Highly recommended!",
                    "rating": star_rating,
                    "tags": ["Attentive Doctor", "Clear Advice", f"{star_rating} Stars"]
                },
                {
                    "title": "Smooth, hygienic and punctual appointment",
                    "review": f"Punctual, hygienic, and thorough checkup with doctor {name} at {company}. Excellent medical care!",
                    "rating": star_rating,
                    "tags": ["Punctual", "Thorough Checkup", "Great Staff"]
                }
            ]
        elif is_realestate:
            raw_list = [
                {
                    "title": "Seamless and transparent property experience",
                    "review": f"Seamless and honest property deal with {name} at {company}{cat_str}. Highly recommended advisor!",
                    "rating": star_rating,
                    "tags": ["Transparent Deal", "Market Expert", "Seamless Process"]
                },
                {
                    "title": "Helped us find the perfect match!",
                    "review": f"{name} understood our exact requirements and found the perfect property at {company}!",
                    "rating": star_rating,
                    "tags": ["Dedicated Advisor", "Prompt Support", "Highly Recommended"]
                },
                {
                    "title": "Professional, reliable and trustworthy",
                    "review": f"Professional, reliable, and transparent property guidance from {name} at {company}. Saved us time!",
                    "rating": star_rating,
                    "tags": ["Trustworthy", "Time Saver", f"{star_rating} Stars"]
                }
            ]
        else:
            raw_list = [
                {
                    "title": f"Exceptional service and quick response{cat_str}",
                    "review": f"Wonderful experience with {name} at {company}{cat_str}! Prompt, professional, and attentive service throughout.",
                    "rating": star_rating,
                    "tags": [tag_prefix, "Top Quality", f"{star_rating} Stars"]
                },
                {
                    "title": "True professional who goes above and beyond",
                    "review": f"{name} was fantastic, polite, and went above and beyond for us at {company}.",
                    "rating": star_rating,
                    "tags": ["Deep Expertise", "Great Support", "Recommended"]
                },
                {
                    "title": "Smooth, reliable and pleasant experience",
                    "review": f"Smooth and hassle-free service from {name} at {company}{cat_str}. Highly recommended to everyone!",
                    "rating": star_rating,
                    "tags": ["Reliable Service", "Customer First", f"{star_rating} Stars"]
                }
            ]
    elif star_rating == 3:
        raw_list = [
            {
                "title": f"Decent experience with scope for improvement{cat_str}",
                "review": f"Average experience with {name} at {company}{cat_str}. Service was decent, though turnaround was slow.",
                "rating": 3,
                "tags": [tag_prefix, "3 Stars", "Constructive Feedback"]
            },
            {
                "title": "Satisfactory service, fair value",
                "review": f"Satisfactory service from {name} at {company}. Met basic expectations with polite staff communication.",
                "rating": 3,
                "tags": ["Satisfactory", "Fair Experience", "3 Stars"]
            },
            {
                "title": "Average experience overall",
                "review": f"Decent overall experience at {company}, though minor coordination delays occurred with {name}.",
                "rating": 3,
                "tags": ["Average Service", "Room to Grow", "3 Stars"]
            }
        ]
    else:
        raw_list = [
            {
                "title": f"Need improvement in communication and service{cat_str}",
                "review": f"My experience with {name} at {company}{cat_str} fell short due to communication delays.",
                "rating": star_rating,
                "tags": [tag_prefix, f"{star_rating} Star", "Feedback"]
            },
            {
                "title": "Service was below expectations",
                "review": f"Service was below expectations at {company}. Encountered unexpected delays during our interaction.",
                "rating": star_rating,
                "tags": ["Customer Feedback", f"{star_rating} Star", "Service Note"]
            },
            {
                "title": "Disappointed with the turnaround time",
                "review": f"Disappointed with slow turnaround from {name} at {company}. Needs better coordination and responsiveness.",
                "rating": star_rating,
                "tags": ["Slow Response", "Feedback", f"{star_rating} Star"]
            }
        ]

    for item in raw_list:
        item["review"] = limit_to_max_words(item["review"], max_words=15)
    return raw_list

