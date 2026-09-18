/**
 * Public Employee Profile Interactive Engine
 * Real-time event analytics tracking, mobile web share, vCard handling, 
 * and Gemini AI Google Review Assistant
 */

document.addEventListener('DOMContentLoaded', () => {
  const profileWrapper = document.querySelector('.fullpage-layout-wrapper') || document.querySelector('.profile-card-container');
  const employeeId = profileWrapper?.getAttribute('data-employee-id');
  const employeeName = profileWrapper?.getAttribute('data-employee-name') || 'Employee Profile';
  const employeeRole = profileWrapper?.getAttribute('data-employee-role') || '';
  const gmbUrl = profileWrapper?.getAttribute('data-gmb-url') || '';
  const profileUrl = profileWrapper?.getAttribute('data-profile-url') || window.location.href;

  // Toast Notification Helper
  const toast = document.getElementById('public-toast-notification');
  const toastMsg = document.getElementById('public-toast-msg');
  let toastTimer = null;

  const showToast = (message, duration = 3400) => {
    if (!toast) return;
    if (toastMsg) toastMsg.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  };

  // Copy to Clipboard with Toast
  const copyToClipboard = async (text, successMsg = 'Link copied to clipboard!') => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const tempInput = document.createElement('input');
        tempInput.value = text;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand('copy');
        document.body.removeChild(tempInput);
      }
      showToast(successMsg);
      return true;
    } catch (err) {
      console.warn('Clipboard copy failed:', err);
      showToast('Copied: ' + text);
      return false;
    }
  };

  // Track CTA & Social clicks
  const logEvent = (eventType) => {
    if (!employeeId) return;

    const payload = JSON.stringify({
      employee_id: employeeId,
      event_type: eventType,
      referrer: document.referrer || 'direct',
    });

    if (navigator.sendBeacon) {
      const blob = new Blob([payload], { type: 'application/json' });
      navigator.sendBeacon('/api/analytics/event', blob);
    } else {
      fetch('/api/analytics/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true,
      }).catch((e) => console.debug('Analytics log error:', e));
    }
  };

  // Track all data-track-event elements
  document.querySelectorAll('[data-track-event]').forEach((elem) => {
    elem.addEventListener('click', function () {
      const eventType = this.getAttribute('data-track-event');
      if (eventType) {
        logEvent(eventType);
      }
    });
  });

  // Direct Google Review Click
  const googleReviewBtn = document.getElementById('btn-google-review');
  if (googleReviewBtn) {
    googleReviewBtn.addEventListener('click', () => {
      logEvent('google_review_click');
    });
  }

  // WhatsApp Click
  const whatsappBtn = document.getElementById('btn-whatsapp');
  if (whatsappBtn) {
    whatsappBtn.addEventListener('click', () => {
      logEvent('whatsapp_click');
    });
  }

  // Save vCard Click
  const vcardBtn = document.getElementById('btn-save-vcard');
  const stickyVcardBtn = document.getElementById('btn-sticky-vcard');
  const handleVcardClick = () => {
    logEvent('vcard_download');
    showToast('Downloading contact card (.vcf)...');
  };
  if (vcardBtn) vcardBtn.addEventListener('click', handleVcardClick);
  if (stickyVcardBtn) stickyVcardBtn.addEventListener('click', handleVcardClick);

  // Universal Share Handler
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${employeeName} - Digital Profile`,
          text: `Connect with ${employeeName} via verified digital profile:`,
          url: profileUrl,
        });
        logEvent('profile_share');
      } catch (err) {
        if (err.name !== 'AbortError') {
          copyToClipboard(profileUrl, 'Profile link copied to clipboard!');
          logEvent('profile_share');
        }
      }
    } else {
      copyToClipboard(profileUrl, 'Profile link copied to clipboard!');
      logEvent('profile_share');
    }
  };

  // Attach share triggers
  const topbarShareBtn = document.getElementById('btn-topbar-share');
  const cardShareBtn = document.getElementById('btn-share-profile-card');
  const legacyShareBtn = document.getElementById('btn-share-profile');
  const copyLinkQrBtn = document.getElementById('btn-copy-link-qr');

  if (topbarShareBtn) topbarShareBtn.addEventListener('click', handleShare);
  if (cardShareBtn) cardShareBtn.addEventListener('click', handleShare);
  if (legacyShareBtn) legacyShareBtn.addEventListener('click', handleShare);
  if (copyLinkQrBtn) {
    copyLinkQrBtn.addEventListener('click', () => {
      copyToClipboard(profileUrl, 'Profile link copied to clipboard!');
      logEvent('profile_share');
    });
  }

  // ==========================================================================
  // Gemini AI Google Review Assistant
  // ==========================================================================
  const aiModal = document.getElementById('ai-review-modal');
  const btnOpenAiReview = document.getElementById('btn-open-ai-review');
  const btnCloseAiModal = document.getElementById('btn-close-ai-modal');
  const aiBackdrop = document.querySelector('.ai-modal-backdrop');
  
  const starPickBtns = document.querySelectorAll('.star-pick-btn');
  const starRatingLabel = document.getElementById('ai-star-rating-label');
  const categoryChips = document.querySelectorAll('.ai-category-chip');
  const toneChips = document.querySelectorAll('.ai-tone-chip');
  const topicInput = document.getElementById('ai-custom-topic-input');
  const btnRegenerate = document.getElementById('btn-regenerate-ai');
  
  const reviewsLoading = document.getElementById('ai-reviews-loading');
  const reviewsList = document.getElementById('ai-reviews-list');
  const selectedTextarea = document.getElementById('ai-selected-review-text');
  const charCounter = document.getElementById('ai-char-count');
  const btnPostGoogle = document.getElementById('btn-copy-and-post-gmb');

  let currentStarRating = 5;
  let selectedCategories = [];
  let currentTone = 'friendly';
  let hasFetchedInitial = false;

  const starRatingLabels = {
    5: "⭐⭐⭐⭐⭐ 5.0 • Outstanding",
    4: "⭐⭐⭐⭐☆ 4.0 • Very Good",
    3: "⭐⭐⭐☆☆ 3.0 • Satisfactory",
    2: "⭐⭐☆☆☆ 2.0 • Needs Improvement",
    1: "⭐☆☆☆☆ 1.0 • Critical Feedback"
  };

  // Open & Close Modal
  const openAiModal = () => {
    if (!aiModal) return;
    aiModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    logEvent('ai_review_modal_open');

    if (!hasFetchedInitial) {
      fetchAiSuggestions();
      hasFetchedInitial = true;
    }
  };

  const closeAiModal = () => {
    if (!aiModal) return;
    aiModal.style.display = 'none';
    document.body.style.overflow = '';
  };

  const btnStickyAiReview = document.getElementById('btn-sticky-ai-review');
  const sheetDragHandle = document.getElementById('sheet-drag-handle');
  const modalContainer = document.querySelector('.ai-modal-container');

  if (btnOpenAiReview) btnOpenAiReview.addEventListener('click', openAiModal);
  if (btnStickyAiReview) btnStickyAiReview.addEventListener('click', openAiModal);
  if (btnCloseAiModal) btnCloseAiModal.addEventListener('click', closeAiModal);
  
  document.querySelectorAll('.btn-open-ai-modal, [data-open-ai-review]').forEach((btn) => {
    btn.addEventListener('click', openAiModal);
  });
  
  if (sheetDragHandle) {
    sheetDragHandle.addEventListener('click', closeAiModal);
    sheetDragHandle.addEventListener('touchend', (e) => {
      e.preventDefault();
      closeAiModal();
    }, { passive: false });
  }

  if (aiBackdrop) {
    aiBackdrop.addEventListener('click', closeAiModal);
    aiBackdrop.addEventListener('touchend', (e) => {
      e.preventDefault();
      closeAiModal();
    }, { passive: false });
  }

  // Touch swipe-down on modal handle/top to dismiss bottom sheet
  if (modalContainer) {
    let modalTouchStartY = 0;
    modalContainer.addEventListener('touchstart', (e) => {
      if (modalContainer.scrollTop <= 5 && e.touches && e.touches[0]) {
        modalTouchStartY = e.touches[0].clientY;
      } else {
        modalTouchStartY = 0;
      }
    }, { passive: true });

    modalContainer.addEventListener('touchend', (e) => {
      if (modalTouchStartY > 0 && e.changedTouches && e.changedTouches[0]) {
        const diffY = e.changedTouches[0].clientY - modalTouchStartY;
        if (diffY > 70) {
          closeAiModal();
        }
      }
    }, { passive: true });
  }

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && aiModal && aiModal.style.display === 'flex') {
      closeAiModal();
    }
  });

  // Interactive 1-to-5 Star Rating Selector
  const updateStarPickerUI = (rating) => {
    starPickBtns.forEach((btn) => {
      const btnStar = parseInt(btn.getAttribute('data-star'), 10);
      if (btnStar <= rating) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
    if (starRatingLabel) {
      starRatingLabel.textContent = starRatingLabels[rating] || `${rating} Stars`;
    }
  };

  starPickBtns.forEach((btn) => {
    btn.addEventListener('click', function () {
      const selectedStars = parseInt(this.getAttribute('data-star'), 10);
      if (selectedStars >= 1 && selectedStars <= 5) {
        currentStarRating = selectedStars;
        updateStarPickerUI(currentStarRating);
        fetchAiSuggestions();
      }
    });

    btn.addEventListener('mouseenter', function () {
      const hoverStar = parseInt(this.getAttribute('data-star'), 10);
      starPickBtns.forEach((b) => {
        const s = parseInt(b.getAttribute('data-star'), 10);
        if (s <= hoverStar) {
          b.classList.add('hover-active');
        } else {
          b.classList.remove('hover-active');
        }
      });
    });

    btn.addEventListener('mouseleave', function () {
      starPickBtns.forEach((b) => b.classList.remove('hover-active'));
    });
  });

  // Business Category Chips Multi-Select Toggle
  categoryChips.forEach((chip) => {
    chip.addEventListener('click', function () {
      this.classList.toggle('active');
      selectedCategories = Array.from(document.querySelectorAll('.ai-category-chip.active'))
        .map((c) => c.getAttribute('data-category'))
        .filter(Boolean);
      fetchAiSuggestions();
    });
  });

  // Tone Switcher
  toneChips.forEach((chip) => {
    chip.addEventListener('click', function () {
      toneChips.forEach((c) => c.classList.remove('active'));
      this.classList.add('active');
      currentTone = this.getAttribute('data-tone') || 'friendly';
      fetchAiSuggestions();
    });
  });

  // Custom Topic Regenerate
  if (btnRegenerate) {
    btnRegenerate.addEventListener('click', () => {
      fetchAiSuggestions();
    });
  }

  if (topicInput) {
    topicInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        fetchAiSuggestions();
      }
    });
  }

  // Update Character Counter
  if (selectedTextarea && charCounter) {
    selectedTextarea.addEventListener('input', function () {
      charCounter.textContent = this.value.length;
    });
  }

  // Fetch AI Review Suggestions from API
  async function fetchAiSuggestions() {
    if (!employeeId) return;

    if (reviewsLoading) reviewsLoading.style.display = 'flex';
    if (reviewsList) reviewsList.style.display = 'none';

    const topic = topicInput?.value.trim() || '';

    try {
      const response = await fetch('/api/ai/suggest-reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeId,
          tone: currentTone,
          topic: topic,
          star_rating: currentStarRating,
          categories: selectedCategories
        }),
      });

      const data = await response.json();
      if (data.success && Array.isArray(data.reviews) && data.reviews.length > 0) {
        renderReviewCards(data.reviews, currentStarRating);
      } else {
        renderFallbackCards(currentStarRating, selectedCategories);
      }
    } catch (err) {
      console.warn('AI suggestions error, using fallback:', err);
      renderFallbackCards(currentStarRating, selectedCategories);
    } finally {
      if (reviewsLoading) reviewsLoading.style.display = 'none';
      if (reviewsList) reviewsList.style.display = 'flex';
    }
  }

  // Helper to render star rating glyphs string
  function getStarGlyphs(count) {
    const filled = '★ '.repeat(count).trim();
    const empty = '☆ '.repeat(5 - count).trim();
    return empty ? `${filled} ${empty}` : filled;
  }

  // Render Review Cards
  function renderReviewCards(reviews, starRating = 5) {
    if (!reviewsList) return;
    reviewsList.innerHTML = '';

    const starDisplay = getStarGlyphs(starRating);

    reviews.forEach((item, index) => {
      const card = document.createElement('div');
      card.className = `ai-review-card ${index === 0 ? 'selected' : ''}`;
      
      const tagsList = item.tags || [`${starRating} Stars`];
      const tagsHtml = tagsList
        .map((tag) => `<span class="ai-card-tag">${escapeHtml(tag)}</span>`)
        .join('');

      card.innerHTML = `
        <div class="ai-card-header-row">
          <div class="ai-card-stars">${starDisplay}</div>
          ${index === 0 ? '<span class="ai-card-selected-badge">✓ Selected</span>' : ''}
        </div>
        <div class="ai-card-title">${escapeHtml(item.title || 'Recommended Experience')}</div>
        <div class="ai-card-text">${escapeHtml(item.review || '')}</div>
        <div class="ai-card-tags-row">${tagsHtml}</div>
      `;

      card.addEventListener('click', () => {
        // Unselect others
        reviewsList.querySelectorAll('.ai-review-card').forEach((c) => {
          c.classList.remove('selected');
          const badge = c.querySelector('.ai-card-selected-badge');
          if (badge) badge.remove();
        });

        // Select this
        card.classList.add('selected');
        const headerRow = card.querySelector('.ai-card-header-row');
        if (headerRow && !headerRow.querySelector('.ai-card-selected-badge')) {
          headerRow.insertAdjacentHTML('beforeend', '<span class="ai-card-selected-badge">✓ Selected</span>');
        }

        // Populate textarea
        if (selectedTextarea) {
          selectedTextarea.value = item.review || '';
          if (charCounter) charCounter.textContent = selectedTextarea.value.length;
          selectedTextarea.focus();
        }
      });

      reviewsList.appendChild(card);
    });

    // Populate first card by default
    if (selectedTextarea && reviews[0]) {
      selectedTextarea.value = reviews[0].review || '';
      if (charCounter) charCounter.textContent = selectedTextarea.value.length;
    }
  }

  // Render Fallback Cards if network is offline
  function renderFallbackCards(starRating = 5, categories = []) {
    const catStr = categories.length > 0 ? ` for ${categories.join(', ')}` : '';
    let fallbackReviews = [];

    if (starRating >= 4) {
      fallbackReviews = [
        {
          title: `Exceptional service & top quality${catStr}`,
          review: `Wonderful experience with ${employeeName}${catStr}! Prompt, professional, and attentive service throughout.`,
          tags: [categories[0] || "Top Quality", `${starRating} Stars`, "Recommended"]
        },
        {
          title: "True professional who goes above and beyond",
          review: `${employeeName} was extremely helpful, polite, and knowledgeable${catStr}. Truly grateful for the support!`,
          tags: ["Deep Expertise", `${starRating} Stars`, "Great Service"]
        },
        {
          title: "Seamless, hassle-free and friendly experience",
          review: `Smooth and hassle-free assistance from ${employeeName}${catStr}. Will definitely recommend to everyone!`,
          tags: ["Friendly", "Smooth Process", "5 Stars"]
        }
      ];
    } else if (starRating === 3) {
      fallbackReviews = [
        {
          title: `Decent experience with scope for improvement${catStr}`,
          review: `Average experience with ${employeeName}${catStr}. Service was decent, though turnaround was slow.`,
          tags: [categories[0] || "Satisfactory", "3 Stars", "Feedback"]
        },
        {
          title: "Satisfactory service, met expectations",
          review: `Satisfactory interaction with ${employeeName}${catStr}. Met basic expectations with polite communication.`,
          tags: ["Average Service", "3 Stars", "Fair"]
        },
        {
          title: "Decent support overall",
          review: `Decent support from ${employeeName}${catStr}, but coordination took longer than expected.`,
          tags: ["Decent Support", "3 Stars", "Room to Grow"]
        }
      ];
    } else {
      fallbackReviews = [
        {
          title: `Need improvement in service and communication${catStr}`,
          review: `Experience with ${employeeName}${catStr} fell short due to communication delays.`,
          tags: [categories[0] || "Feedback", `${starRating} Star`, "Customer Note"]
        },
        {
          title: "Service was below expectations",
          review: `Service was below expectations with ${employeeName}${catStr}. Hoping for better turnaround next time.`,
          tags: ["Customer Feedback", `${starRating} Star`]
        },
        {
          title: "Disappointed with turnaround time",
          review: `Disappointed with slow communication from ${employeeName}${catStr}. Needs better responsiveness.`,
          tags: ["Slow Response", `${starRating} Star`]
        }
      ];
    }

    renderReviewCards(fallbackReviews, starRating);
  }

  // Helper to ensure Google Review link triggers the 5-star Write Review popup dialog
  const getDirectGoogleReviewUrl = (rawUrl) => {
    if (!rawUrl) return 'https://google.com';
    let url = rawUrl.trim();
    if (url.includes('lrd=')) {
      url = url.replace(/(lrd=[a-zA-Z0-9_xX:]+),1/g, '$1,3');
    }
    return url;
  };

  // 1-Click Copy and Post to Google My Business
  if (btnPostGoogle) {
    btnPostGoogle.addEventListener('click', async () => {
      const reviewText = selectedTextarea?.value.trim() || '';
      const targetGmbUrl = getDirectGoogleReviewUrl(gmbUrl);

      if (!reviewText) {
        showToast('Please select or type a review first!');
        return;
      }

      // Copy text to clipboard
      await copyToClipboard(reviewText, 'Review copied! Just paste (Ctrl+V) on Google.');

      // Button UI Animation Feedback
      btnPostGoogle.classList.add('copied-state');
      btnPostGoogle.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
        <span>✓ Copied! Opening Google Reviews...</span>
      `;

      logEvent('ai_review_copied_gmb_click');

      // Open Google Review URL in new tab after brief 350ms tick
      setTimeout(() => {
        window.open(targetGmbUrl, '_blank');
        
        // Reset button state
        setTimeout(() => {
          btnPostGoogle.classList.remove('copied-state');
          btnPostGoogle.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>🚀 Copy & Post on Google</span>
          `;
        }, 2500);
      }, 350);
    });
  }

  // ==========================================================================
  // Visitor Lead Capture Modal Handler
  // ==========================================================================
  const leadModal = document.getElementById('visitor-lead-modal');
  const leadForm = document.getElementById('visitor-lead-form');
  const btnCloseLeadModal = document.getElementById('btn-close-lead-modal');
  const btnSkipLeadModal = document.getElementById('btn-skip-lead-modal');
  const leadBackdrop = leadModal?.querySelector('.lead-modal-backdrop');
  const leadDragHandle = document.getElementById('lead-sheet-drag-handle');
  const btnFloatingLeadTrigger = document.getElementById('btn-floating-lead-trigger');
  const leadFormError = document.getElementById('lead-form-error');
  const btnSubmitLead = document.getElementById('btn-submit-lead-form');
  const leadContainer = leadModal?.querySelector('.lead-modal-container');

  const openLeadModal = () => {
    if (!leadModal) return;
    leadModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    logEvent('lead_modal_open');
  };

  const closeLeadModal = () => {
    if (!leadModal) return;
    leadModal.style.display = 'none';
    document.body.style.overflow = '';
    if (leadFormError) {
      leadFormError.style.display = 'none';
      leadFormError.textContent = '';
    }
  };

  if (btnCloseLeadModal) btnCloseLeadModal.addEventListener('click', closeLeadModal);
  if (btnSkipLeadModal) btnSkipLeadModal.addEventListener('click', closeLeadModal);
  if (btnFloatingLeadTrigger) btnFloatingLeadTrigger.addEventListener('click', openLeadModal);
  if (leadBackdrop) leadBackdrop.addEventListener('click', closeLeadModal);

  if (leadDragHandle) {
    leadDragHandle.addEventListener('click', closeLeadModal);
    leadDragHandle.addEventListener('touchend', (e) => {
      e.preventDefault();
      closeLeadModal();
    }, { passive: false });
  }

  // Swipe-down to close on touch devices
  if (leadContainer) {
    let leadTouchStartY = 0;
    leadContainer.addEventListener('touchstart', (e) => {
      if (leadContainer.scrollTop <= 5 && e.touches && e.touches[0]) {
        leadTouchStartY = e.touches[0].clientY;
      } else {
        leadTouchStartY = 0;
      }
    }, { passive: true });

    leadContainer.addEventListener('touchend', (e) => {
      if (leadTouchStartY > 0 && e.changedTouches && e.changedTouches[0]) {
        const diffY = e.changedTouches[0].clientY - leadTouchStartY;
        if (diffY > 70) {
          closeLeadModal();
        }
      }
    }, { passive: true });
  }

  // Handle Form Submission
  if (leadForm) {
    leadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (leadFormError) {
        leadFormError.style.display = 'none';
        leadFormError.textContent = '';
      }

      const name = document.getElementById('lead-name')?.value.trim();
      const phone = document.getElementById('lead-phone')?.value.trim();
      const email = document.getElementById('lead-email')?.value.trim();
      const dob = document.getElementById('lead-dob')?.value.trim();
      const anniversary = document.getElementById('lead-anniversary')?.value.trim();
      const city = document.getElementById('lead-city')?.value.trim();

      // Basic client validation
      if (!name) {
        showLeadError('Please enter your full name.');
        return;
      }
      if (!phone || phone.replace(/\D/g, '').length < 7) {
        showLeadError('Please enter a valid mobile number (at least 7 digits).');
        return;
      }
      if (!email || !email.includes('@') || !email.includes('.')) {
        showLeadError('Please enter a valid email address.');
        return;
      }

      // Button loading state
      const originalBtnHtml = btnSubmitLead ? btnSubmitLead.innerHTML : '';
      if (btnSubmitLead) {
        btnSubmitLead.disabled = true;
        btnSubmitLead.innerHTML = `
          <svg class="spinner-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle><path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path></svg>
          <span>Saving...</span>
        `;
      }

      try {
        const response = await fetch('/api/leads/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            employee_id: employeeId,
            name: name,
            phone: phone,
            email: email,
            dob: dob || null,
            anniversary: anniversary || null,
            city: city || null,
            source: window.location.pathname.startsWith('/q/') ? 'qr_scan' : 'direct_web'
          })
        });

        const result = await response.json();

        if (response.ok && result.success) {
          showToast(result.message || 'Thank you for connecting!', 4500);
          leadForm.reset();
          closeLeadModal();
        } else {
          showLeadError(result.message || 'Failed to submit details. Please check your information.');
        }
      } catch (err) {
        console.error('Lead submit error:', err);
        showLeadError('Unable to connect to server. Please try again.');
      } finally {
        if (btnSubmitLead) {
          btnSubmitLead.disabled = false;
          btnSubmitLead.innerHTML = originalBtnHtml;
        }
      }
    });
  }

  function showLeadError(msg) {
    if (leadFormError) {
      leadFormError.textContent = msg;
      leadFormError.style.display = 'block';
    } else {
      showToast(msg);
    }
  }

  // Auto-open lead modal on every page visit / refresh
  if (leadModal && employeeId) {
    setTimeout(() => {
      openLeadModal();
    }, 250);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});


