import json
import logging
import random
import re
import urllib.request
import urllib.error
from config import Config

logger = logging.getLogger(__name__)

def sanitize_review_text(text, company_name=None):
    """
    Strips any unwanted platform or agency company names like 'Nexalogic Techno'
    or 'at Nexalogic Techno' from review text.
    """
    if not text:
        return ""
    targets = ['Nexalogic Techno', 'NexalogicTechno', 'Nexalogic']
    if company_name and isinstance(company_name, str) and company_name.strip():
        c_clean = company_name.strip()
        if c_clean.lower() not in [t.lower() for t in targets]:
            targets.append(c_clean)
            
    cleaned = str(text)
    for t in targets:
        cleaned = re.sub(rf'\b(?:at|with|from|by)\s+{re.escape(t)}[!?,.]*\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(rf'\b{re.escape(t)}[!?,.]*\b', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s+([!?,.])', r'\1', cleaned)
    return cleaned.strip()


def limit_to_max_words(text, max_words=15):
    """Ensures text strictly has at most max_words words without awkward trailing prepositions."""
    if not text:
        return ""
    words = str(text).strip().split()
    if len(words) <= max_words:
        return str(text).strip()
    truncated = " ".join(words[:max_words]).rstrip(",;:- ")
    trailing_words = {'the', 'with', 'and', 'for', 'of', 'in', 'to', 'a', 'an', 'at', 'by', 'our', 'my'}
    while truncated.split() and truncated.split()[-1].lower() in trailing_words:
        truncated = " ".join(truncated.split()[:-1]).rstrip(",;:- ")
    return truncated.rstrip(".!?,") + "."


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
    Generates 3 context-aware, highly varied Google Review suggestions using Gemini AI API
    tailored to specific employee details, star ratings (1 to 5), and business domains.
    STRICT CONSTRAINT: Maximum 15 words per review suggestion.
    NO MENTION OF NEXALOGIC TECHNO OR PLATFORM COMPANY NAME.
    Falls back gracefully to intelligent, randomized domain-tailored templates if API is unreachable.
    """
    api_key = Config.GEMINI_API_KEY
    
    employee_name = employee_name or 'the team member'
    first_name = employee_name.split()[0] if employee_name else 'Professional'
    designation = designation or 'Professional'
    
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

    focus_str = custom_topic if custom_topic else (", ".join(cat_list[:2]) if cat_list else "Customer Service")

    prompt = (
        f"Generate 3 completely DISTINCT, REALISTIC Google Review suggestions for a customer to leave about {employee_name}, "
        f"working as a {designation}.\n"
        f"Target Rating: {rating_guide}\n"
        f"Role / Professional Context: {bio or designation}\n"
        f"Focus Area: {focus_str}\n"
        f"Tone: {tone_guide}\n\n"
        f"CRITICAL REQUIREMENTS:\n"
        f"1. DIVERSITY: Each review MUST take a completely distinct perspective:\n"
        f"   - Suggestion 1: Focus on speed, prompt communication, and responsiveness.\n"
        f"   - Suggestion 2: Focus on deep expertise, honest guidance, and quality as a {designation}.\n"
        f"   - Suggestion 3: Focus on friendly demeanor, customer care, and going above & beyond.\n"
        f"2. LENGTH: Each 'review' MUST be STRICTLY 10 TO 15 WORDS. Punchy, short, real human speech. Under 15 words.\n"
        f"3. STRICT CONSTRAINT: NEVER mention 'Nexalogic Techno', 'Nexalogic', or any platform agency name.\n"
        f"4. Output STRICTLY a JSON array of 3 objects with:\n"
        f"   - 'title': Short catchy headline (2 to 5 words)\n"
        f"   - 'review': Punchy review text (STRICTLY MAXIMUM 15 WORDS)\n"
        f"   - 'rating': Integer {star_rating}\n"
        f"   - 'tags': Array of 2-3 short highlight tags\n"
    )

    if api_key and not api_key.startswith('your_'):
        # Prioritize ultra-fast and reliable models with quick 3.5s timeout
        models_to_try = ['gemini-3.1-flash-lite', 'gemini-flash-lite-latest']

        for mod in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.9,
                    "maxOutputTokens": 2048
                }
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=3.5) as response:
                    if response.status == 200:
                        raw_data = response.read().decode('utf-8')
                        resp_json = json.loads(raw_data)
                        text_content = resp_json['candidates'][0]['content']['parts'][0]['text']
                        parsed_reviews = json.loads(text_content)
                        if isinstance(parsed_reviews, list) and len(parsed_reviews) > 0:
                            sanitized = []
                            for item in parsed_reviews[:3]:
                                raw_review = str(item.get("review", "")).strip()
                                cleaned_review = sanitize_review_text(raw_review, company_name)
                                trimmed_review = limit_to_max_words(cleaned_review, max_words=15)
                                sanitized_title = sanitize_review_text(str(item.get("title", "Recommended Experience")).strip(), company_name)
                                sanitized.append({
                                    "title": sanitized_title or "Recommended Experience",
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

    # Fallback to rich, randomized domain-aware templates
    return {
        "success": True,
        "source": "smart_fallback",
        "star_rating": star_rating,
        "reviews": generate_fallback_reviews(employee_name, designation, company_name, custom_topic, star_rating, cat_list)
    }


def generate_fallback_reviews(name, designation, company="", topic="", star_rating=5, categories=None):
    """
    Provides rich, domain-aware, and highly randomized fallback reviews.
    Every generation samples from an extensive pool of short (max 15 words) reviews
    customized to the employee's role and details.
    """
    first_name = name.split()[0] if name else "Professional"
    role = designation if designation else "Executive"
    topic_clean = topic.strip() if topic else ""
    tag_prefix = (categories[0] if categories else "Top Quality")
    
    desig_lower = (designation or "").lower()
    
    # Identify domain
    is_sales = any(k in desig_lower for k in ['sales', 'executive', 'business development', 'bd', 'growth', 'consultant', 'account'])
    is_doctor = any(k in desig_lower for k in ['doctor', 'dr', 'physician', 'surgeon', 'dentist', 'clinic', 'medical', 'nurse'])
    is_tech = any(k in desig_lower for k in ['developer', 'engineer', 'tech', 'software', 'it', 'coder', 'architect'])
    is_realestate = any(k in desig_lower for k in ['real estate', 'realtor', 'property', 'broker', 'housing', 'builder'])
    is_clothing = any(k in desig_lower for k in ['menswear', 'clothing', 'fashion', 'tailor', 'suit', 'fabric', 'apparel'])
    is_auto = any(k in desig_lower for k in ['service advisor', 'mechanic', 'auto', 'car', 'bike', 'workshop', 'motors'])

    if star_rating >= 4:
        if is_sales:
            pool = [
                {
                    "title": "Prompt guidance and genuine advice",
                    "review": f"Very prompt, honest, and professional sales advice from {name}. Made everything seamless and clear.",
                    "tags": ["Sales Advisory", "Prompt Service", f"{star_rating} Stars"]
                },
                {
                    "title": "Truly exceptional customer support",
                    "review": f"{name} understood our exact requirements and delivered the best solution. Truly pleased!",
                    "tags": ["Great Listener", "Top Solution", "Recommended"]
                },
                {
                    "title": "Fast, clear and reliable consultation",
                    "review": f"Quick responses and transparent consultation from {name}. Saved us valuable time and effort.",
                    "tags": ["Time Saver", "Transparent", f"{star_rating} Stars"]
                },
                {
                    "title": "Goes above and beyond for clients",
                    "review": f"{first_name} was courteous, patient, and went above and beyond to answer all our questions.",
                    "tags": ["Helpful Staff", "Dedicated", f"{star_rating} Stars"]
                },
                {
                    "title": "Hassle-free and pleasant experience",
                    "review": f"Wonderful experience dealing with {name}. Knowledgeable, courteous, and very efficient throughout.",
                    "tags": ["Hassle Free", "Deep Knowledge", "5 Stars"]
                },
                {
                    "title": "Highly recommended sales professional",
                    "review": f"Outstanding assistance from {name}! Honest approach and very responsive communication at every step.",
                    "tags": ["Honest Advice", "Fast Response", "Recommended"]
                },
                {
                    "title": "Smooth coordination and great value",
                    "review": f"{name} handled our request smoothly with zero delay. Appreciate the high standard of work!",
                    "tags": ["Smooth Process", "High Standards", f"{star_rating} Stars"]
                }
            ]
        elif is_doctor:
            pool = [
                {
                    "title": "Compassionate care and thorough explanation",
                    "review": f"Outstanding care by {name}. Extremely compassionate, attentive, and explained the diagnosis very clearly.",
                    "tags": ["Compassionate Care", "Clear Diagnosis", f"{star_rating} Stars"]
                },
                {
                    "title": "Patience and great clinical expertise",
                    "review": f"{first_name} listened patiently to all concerns and provided genuine medical guidance. Highly recommended!",
                    "tags": ["Patient Doctor", "Great Advice", "Recommended"]
                },
                {
                    "title": "Very reassuring and professional consultation",
                    "review": f"Felt very comfortable and well assisted by {name}. Calm demeanor and prompt attention.",
                    "tags": ["Calm Demeanor", "Professional Care", f"{star_rating} Stars"]
                },
                {
                    "title": "Dedicated medical guidance",
                    "review": f"{name} gave precise advice and timely treatment. Truly appreciative of the dedicated care.",
                    "tags": ["Precise Advice", "Top Care", "5 Stars"]
                }
            ]
        elif is_tech:
            pool = [
                {
                    "title": "Outstanding technical expertise",
                    "review": f"{name} solved our technical requirements quickly and with remarkable precision. Highly skilled engineer!",
                    "tags": ["Technical Skills", "Fast Delivery", f"{star_rating} Stars"]
                },
                {
                    "title": "Prompt and clear communication",
                    "review": f"Great technical guidance and rapid implementation from {name}. Made complex problem-solving look effortless.",
                    "tags": ["Clear Comm", "Problem Solver", "Recommended"]
                },
                {
                    "title": "Delivered on time with high quality",
                    "review": f"Working with {first_name} was seamless. High-quality code delivery and exceptional attention to detail.",
                    "tags": ["High Quality", "Reliable", f"{star_rating} Stars"]
                }
            ]
        elif is_realestate:
            pool = [
                {
                    "title": "Transparent and honest property guidance",
                    "review": f"Transparent consultation and smooth documentation support from {name}. Guided us without any pressure.",
                    "tags": ["Honest Broker", "Smooth Closing", f"{star_rating} Stars"]
                },
                {
                    "title": "Saved us valuable time",
                    "review": f"{name} showed verified options matching our exact budget. Very reliable property professional!",
                    "tags": ["Verified Properties", "Time Saver", "Recommended"]
                },
                {
                    "title": "Effortless property journey",
                    "review": f"Very trustworthy and clear communication from {name}. Made our property journey completely hassle-free.",
                    "tags": ["Trustworthy", "Hassle Free", f"{star_rating} Stars"]
                }
            ]
        elif is_clothing:
            pool = [
                {
                    "title": "Outstanding craftsmanship and fitting",
                    "review": f"Incredible experience shopping with {name}! Top quality fabric and perfect custom fitting results.",
                    "tags": ["Custom Fitting", "Top Quality", f"{star_rating} Stars"]
                },
                {
                    "title": "Superb collection and great support",
                    "review": f"{name} was super helpful and knowledgeable about current trends. Found exactly what I needed!",
                    "tags": ["Great Collection", "Helpful Staff", "Recommended"]
                },
                {
                    "title": "Fast turnaround and flawless service",
                    "review": f"Fast delivery and exceptional styling advice from {first_name}. Highly recommend to everyone!",
                    "tags": ["Fast Delivery", "Styling Advice", f"{star_rating} Stars"]
                }
            ]
        elif is_auto:
            pool = [
                {
                    "title": "Honest vehicle diagnosis and prompt delivery",
                    "review": f"Prompt vehicle inspection and honest advice from {name}. Service delivered right on time.",
                    "tags": ["Prompt Service", "Honest Advice", f"{star_rating} Stars"]
                },
                {
                    "title": "Transparent cost and courteous communication",
                    "review": f"{name} explained all repairs clearly without unnecessary expenses. Great service experience!",
                    "tags": ["Transparent Cost", "Courteous Staff", "Recommended"]
                }
            ]
        else:
            pool = [
                {
                    "title": "Prompt, polite and professional service",
                    "review": f"Wonderful experience with {name}! Prompt, professional, and attentive service throughout our interaction.",
                    "tags": [tag_prefix, "Prompt Service", f"{star_rating} Stars"]
                },
                {
                    "title": "True professional who goes above and beyond",
                    "review": f"{name} was fantastic, polite, and went above and beyond to ensure complete satisfaction.",
                    "tags": ["Deep Expertise", "Great Support", "Recommended"]
                },
                {
                    "title": "Smooth, reliable and pleasant experience",
                    "review": f"Smooth and hassle-free assistance from {name}. Highly recommended to everyone looking for quality!",
                    "tags": ["Reliable Service", "Customer First", f"{star_rating} Stars"]
                },
                {
                    "title": "Clear communication and fast turnaround",
                    "review": f"Delightful experience working with {first_name}. Quick answers, transparent updates, and genuine dedication.",
                    "tags": ["Quick Answers", "Dedicated", "Top Quality"]
                },
                {
                    "title": "Top-tier assistance and friendly attitude",
                    "review": f"{name} made the entire process effortless. Courteous demeanor and great attention to detail.",
                    "tags": ["Effortless Process", "Courteous", f"{star_rating} Stars"]
                }
            ]
    elif star_rating == 3:
        pool = [
            {
                "title": "Decent service with room for improvement",
                "review": f"Average experience with {name}. Service was satisfactory, though turnaround communication could be quicker.",
                "tags": ["Average Service", "3 Stars", "Feedback"]
            },
            {
                "title": "Satisfactory support, fair value",
                "review": f"Met basic expectations with polite staff coordination from {first_name}. Decent overall interaction.",
                "tags": ["Satisfactory", "Fair Experience", "3 Stars"]
            },
            {
                "title": "Moderate experience overall",
                "review": f"Service from {name} was acceptable, though minor coordination delays occurred during the process.",
                "tags": ["Moderate Service", "Room to Grow", "3 Stars"]
            },
            {
                "title": "Polite staff with minor delays",
                "review": f"{name} was polite and answered queries, but response times could definitely be improved.",
                "tags": ["Polite Staff", "Minor Delays", "3 Stars"]
            }
        ]
    else:
        pool = [
            {
                "title": "Needs improvement in communication",
                "review": f"My experience with {name} fell short due to communication delays and slower turnaround.",
                "tags": [f"{star_rating} Star", "Feedback", "Customer Note"]
            },
            {
                "title": "Service was below expectations",
                "review": f"Encountered unexpected delays during interaction with {name}. Needs better proactive coordination.",
                "tags": ["Customer Feedback", f"{star_rating} Star", "Service Note"]
            },
            {
                "title": "Disappointed with turnaround time",
                "review": f"Disappointed with slow turnaround from {first_name}. Requires better responsiveness to client queries.",
                "tags": ["Slow Response", "Feedback", f"{star_rating} Star"]
            }
        ]

    # Dynamically select 3 different reviews from the pool
    sample_count = min(3, len(pool))
    selected = random.sample(pool, sample_count)
    
    # If pool had fewer than 3, duplicate or pad safely
    while len(selected) < 3 and pool:
        selected.append(pool[len(selected) % len(pool)])

    for item in selected:
        clean_text = sanitize_review_text(item["review"], company)
        item["review"] = limit_to_max_words(clean_text, max_words=15)
        item["title"] = sanitize_review_text(item["title"], company)
        item["rating"] = star_rating

    return selected
