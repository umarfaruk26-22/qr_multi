/**
 * WYDdigi-Style Public Profile Interactive Engine
 * Seamless Dual-Gate Review Routing:
 * - 1-3 Stars: Captures private feedback form (Negative Shield)
 * - 4-5 Stars: Generates single short AI review, copies to clipboard, and directly redirects to Google Reviews!
 */

document.addEventListener('DOMContentLoaded', () => {
  const profileWrapper = document.querySelector('.fullpage-layout-wrapper');
  const employeeId = profileWrapper?.getAttribute('data-employee-id');
  const employeeName = profileWrapper?.getAttribute('data-employee-name') || 'Team Member';
  const employeeRole = profileWrapper?.getAttribute('data-employee-role') || '';
  const rawGmbUrl = profileWrapper?.getAttribute('data-gmb-url') || '';
  const profileUrl = profileWrapper?.getAttribute('data-profile-url') || window.location.href;

  // Format Google Review direct popup URL
  const getDirectGoogleReviewUrl = (rawUrl) => {
    if (!rawUrl) return 'https://google.com';
    let url = rawUrl.trim();
    if (url.includes('lrd=')) {
      url = url.replace(/(lrd=[a-zA-Z0-9_xX:]+),1/g, '$1,3');
    }
    return url;
  };

  const targetGmbUrl = getDirectGoogleReviewUrl(rawGmbUrl);

  // Toast Notification Helper
  const toast = document.getElementById('public-toast-notification');
  const toastMsg = document.getElementById('public-toast-msg');
  let toastTimer = null;

  const showToast = (message, duration = 3000) => {
    if (!toast) return;
    if (toastMsg) toastMsg.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  };

  // Copy to Clipboard
  const copyToClipboard = async (text, successMsg = 'Copied to clipboard!') => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const tempInput = document.createElement('textarea');
        tempInput.value = text;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand('copy');
        document.body.removeChild(tempInput);
      }
      if (successMsg) showToast(successMsg);
      return true;
    } catch (err) {
      console.warn('Clipboard copy failed:', err);
      if (successMsg) showToast('Copied: ' + text);
      return false;
    }
  };

  // Analytics event tracker
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

  // Track data-track-event elements
  document.querySelectorAll('[data-track-event]').forEach((elem) => {
    elem.addEventListener('click', function () {
      const evt = this.getAttribute('data-track-event');
      if (evt) logEvent(evt);
    });
  });

  // Web Share or Copy Link Helper
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: document.title,
          text: `Connect with ${employeeName}`,
          url: profileUrl,
        });
        logEvent('profile_shared');
        return;
      } catch (err) {
        if (err.name === 'AbortError') return;
      }
    }
    copyToClipboard(profileUrl, 'Profile link copied to clipboard!');
    logEvent('profile_link_copied');
  };

  const topbarShareBtn = document.getElementById('btn-topbar-share');
  if (topbarShareBtn) topbarShareBtn.addEventListener('click', handleShare);

  const cardShareBtn = document.getElementById('btn-share-profile-card');
  if (cardShareBtn) cardShareBtn.addEventListener('click', handleShare);

  const qrCopyLinkBtn = document.getElementById('btn-copy-link-qr');
  if (qrCopyLinkBtn) {
    qrCopyLinkBtn.addEventListener('click', () => {
      copyToClipboard(profileUrl, 'Profile link copied to clipboard!');
      logEvent('qr_link_copied');
    });
  }

  // ==========================================================================
  // WYDdigi Style Review Logic
  // ==========================================================================
  const starsContainer = document.getElementById('wyddigi-stars-picker');
  const stars = document.querySelectorAll('.wyddigi-star');
  const starHint = document.getElementById('wyddigi-star-hint');
  
  const negativeBox = document.getElementById('negative-feedback-container');
  const negativeForm = document.getElementById('negative-feedback-form');
  const negativeSuccess = document.getElementById('negative-feedback-success');
  const negativeRatingInput = document.getElementById('negative-form-rating');

  const reviewModal = document.getElementById('wyddigi-review-modal');
  const btnCloseReviewModal = document.getElementById('btn-close-wyddigi-modal');
  const modalReviewLoading = document.getElementById('modal-review-loading');
  const modalReviewTextWrap = document.getElementById('modal-review-text-wrap');
  const modalSingleReviewText = document.getElementById('modal-single-review-text');
  const btnCopyReviewDirect = document.getElementById('btn-copy-review-direct');
  const btnCopyTextLabel = document.getElementById('btn-copy-text-label');
  const btnTryAnotherReview = document.getElementById('btn-try-another-review');
  const modalCountdown = document.getElementById('modal-redirect-countdown');
  const countdownSeconds = document.getElementById('countdown-seconds');

  let selectedRating = 0;
  let currentGeneratedReview = '';
  let redirectCountdownTimer = null;

  // Star ratings hover and selection
  if (starsContainer) {
    stars.forEach((star) => {
      star.addEventListener('mouseenter', function () {
        const rating = parseInt(this.getAttribute('data-rating'), 10);
        highlightStars(rating, true);
        updateStarHint(rating);
      });

      star.addEventListener('mouseleave', function () {
        highlightStars(selectedRating, false);
        updateStarHint(selectedRating);
      });

      star.addEventListener('click', function () {
        const rating = parseInt(this.getAttribute('data-rating'), 10);
        selectedRating = rating;
        highlightStars(selectedRating, false);
        handleRatingSelection(selectedRating);
      });
    });
  }

  function highlightStars(count, isHover = false) {
    stars.forEach((s) => {
      const r = parseInt(s.getAttribute('data-rating'), 10);
      s.classList.remove('hovered', 'active');
      if (r <= count) {
        s.classList.add(isHover ? 'hovered' : 'active');
      }
    });
  }

  function updateStarHint(rating) {
    if (!starHint) return;
    const hints = {
      1: '1 Star • Need Improvements',
      2: '2 Stars • Below Expectations',
      3: '3 Stars • Average Experience',
      4: '4 Stars • Very Good!',
      5: '5 Stars • Outstanding Excellence!'
    };
    starHint.textContent = hints[rating] || 'Tap a star to rate';
  }

  // Handle Dual-Gate Routing
  function handleRatingSelection(rating) {
    logEvent(`star_rating_selected_${rating}`);

    if (rating <= 3) {
      // Gate A: Negative / Critical Review -> Reveal private feedback form (Shield Google)
      if (negativeBox) {
        negativeBox.style.display = 'block';
        if (negativeSuccess) negativeSuccess.style.display = 'none';
        if (negativeForm) negativeForm.style.display = 'flex';
        if (negativeRatingInput) negativeRatingInput.value = rating;

        negativeBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    } else {
      // Gate B: Positive Review (4 or 5 Stars) -> Open WYDdigi Review Generator Screen
      if (negativeBox) negativeBox.style.display = 'none';
      openPositiveReviewScreen(rating);
    }
  }

  // Submit Negative Feedback (Shielded)
  if (negativeForm) {
    negativeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('btn-submit-negative-feedback');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Submitting...</span>`;
      }

      const formData = new FormData(negativeForm);
      const payload = {
        employee_id: employeeId,
        name: formData.get('name'),
        phone: formData.get('phone'),
        email: formData.get('email') || '',
        city: `Rating: ${formData.get('rating')} Stars - Feedback: ${formData.get('feedback')}`,
        source: 'negative_review_gate'
      };

      try {
        const res = await fetch('/api/leads/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          negativeForm.style.display = 'none';
          if (negativeSuccess) negativeSuccess.style.display = 'block';
          logEvent('negative_feedback_saved');
        } else {
          alert(data.message || 'Error submitting feedback. Please try again.');
        }
      } catch (err) {
        console.error('Feedback submit failed:', err);
        // Fallback friendly success
        negativeForm.style.display = 'none';
        if (negativeSuccess) negativeSuccess.style.display = 'block';
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<span>Submit Feedback</span>`;
        }
      }
    });
  }

  // ==========================================================================
  // Positive Review Generator Flow (4 & 5 Stars)
  // ==========================================================================
  async function openPositiveReviewScreen(starRating = 5) {
    if (!reviewModal) return;
    reviewModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Reset view states
    if (modalReviewLoading) modalReviewLoading.style.display = 'flex';
    if (modalReviewTextWrap) modalReviewTextWrap.style.display = 'none';
    if (modalCountdown) modalCountdown.style.display = 'none';
    if (btnCopyTextLabel) btnCopyTextLabel.textContent = 'COPY REVIEW';
    if (btnCopyReviewDirect) btnCopyReviewDirect.classList.remove('copied-state');

    await fetchSingleShortReview(starRating);
  }

  async function fetchSingleShortReview(starRating = 5) {
    try {
      const res = await fetch('/api/ai/suggest-reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeId,
          tone: 'friendly',
          star_rating: starRating,
          single: true
        })
      });

      const data = await res.json();
      let review = '';
      if (data.success && data.single_review && data.single_review.review) {
        review = data.single_review.review;
      } else if (data.success && Array.isArray(data.reviews) && data.reviews.length > 0) {
        review = data.reviews[0].review;
      } else {
        review = `Prompt, courteous, and wonderful experience with ${employeeName}. Highly recommended!`;
      }

      // Sanitize review text
      currentGeneratedReview = String(review).replace(/\s+/g, ' ').trim();
      renderSingleReview(currentGeneratedReview);

    } catch (err) {
      console.warn('AI review fetch failed, using smart fallback:', err);
      currentGeneratedReview = `Smooth, professional, and excellent service from ${employeeName}. Highly recommended!`;
      renderSingleReview(currentGeneratedReview);
    }
  }

  function renderSingleReview(text) {
    if (modalReviewLoading) modalReviewLoading.style.display = 'none';
    if (modalReviewTextWrap) modalReviewTextWrap.style.display = 'block';
    if (modalSingleReviewText) modalSingleReviewText.textContent = text;

    // Start auto-redirect countdown
    startRedirectCountdown();
  }

  function startRedirectCountdown() {
    clearInterval(redirectCountdownTimer);
    let secondsLeft = 3;
    if (modalCountdown) modalCountdown.style.display = 'block';
    if (countdownSeconds) countdownSeconds.textContent = secondsLeft;

    redirectCountdownTimer = setInterval(() => {
      secondsLeft -= 1;
      if (countdownSeconds) countdownSeconds.textContent = secondsLeft;

      if (secondsLeft <= 0) {
        clearInterval(redirectCountdownTimer);
        // Execute copy and redirect automatically!
        executeCopyAndRedirect();
      }
    }, 1000);
  }

  // Copy Review and Direct Redirect to Google Target Link
  async function executeCopyAndRedirect() {
    clearInterval(redirectCountdownTimer);
    if (!currentGeneratedReview) {
      currentGeneratedReview = modalSingleReviewText?.textContent.trim() || `Great service from ${employeeName}!`;
    }

    // 1. Copy text to clipboard
    await copyToClipboard(currentGeneratedReview, '✓ Review Copied! Opening Google Reviews...');

    // 2. UI feedback
    if (btnCopyReviewDirect) {
      btnCopyReviewDirect.classList.add('copied-state');
      if (btnCopyTextLabel) btnCopyTextLabel.textContent = '✓ COPIED! REDIRECTING...';
    }

    logEvent('positive_review_copied_gmb_redirect');

    // 3. Immediately redirect to target Google Review link
    setTimeout(() => {
      window.location.href = targetGmbUrl;
    }, 600);
  }

  // Button Click: COPY REVIEW & GO TO GOOGLE
  if (btnCopyReviewDirect) {
    btnCopyReviewDirect.addEventListener('click', (e) => {
      e.preventDefault();
      executeCopyAndRedirect();
    });
  }

  // Try Another Review
  if (btnTryAnotherReview) {
    btnTryAnotherReview.addEventListener('click', async () => {
      clearInterval(redirectCountdownTimer);
      if (modalReviewLoading) modalReviewLoading.style.display = 'flex';
      if (modalReviewTextWrap) modalReviewTextWrap.style.display = 'none';
      if (modalCountdown) modalCountdown.style.display = 'none';
      await fetchSingleShortReview(selectedRating || 5);
    });
  }

  // Close Positive Review Screen
  if (btnCloseReviewModal) {
    btnCloseReviewModal.addEventListener('click', () => {
      clearInterval(redirectCountdownTimer);
      if (reviewModal) reviewModal.style.display = 'none';
      document.body.style.overflow = '';
    });
  }

  // Close modal when backdrop clicked
  const reviewModalBackdrop = document.querySelector('.wyddigi-modal-backdrop');
  if (reviewModalBackdrop) {
    reviewModalBackdrop.addEventListener('click', () => {
      clearInterval(redirectCountdownTimer);
      if (reviewModal) reviewModal.style.display = 'none';
      document.body.style.overflow = '';
    });
  }

  // ==========================================================================
  // Visitor Lead Modal (General Connect Form)
  // ==========================================================================
  const leadModal = document.getElementById('visitor-lead-modal');
  const btnFloatingLead = document.getElementById('btn-floating-lead-trigger');
  const btnCloseLeadModal = document.getElementById('btn-close-lead-modal');
  const leadForm = document.getElementById('visitor-lead-form');
  const leadFormError = document.getElementById('lead-form-error');

  if (btnFloatingLead && leadModal) {
    btnFloatingLead.addEventListener('click', () => {
      leadModal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    });
  }

  if (btnCloseLeadModal && leadModal) {
    btnCloseLeadModal.addEventListener('click', () => {
      leadModal.style.display = 'none';
      document.body.style.overflow = '';
    });
  }

  if (leadForm) {
    leadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('btn-submit-lead-form');
      if (submitBtn) submitBtn.disabled = true;

      const formData = new FormData(leadForm);
      const payload = {
        employee_id: employeeId,
        name: formData.get('name'),
        phone: formData.get('phone'),
        email: formData.get('email') || '',
        source: 'floating_connect_modal'
      };

      try {
        const res = await fetch('/api/leads/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          showToast(`Thank you ${payload.name}, your details were sent!`);
          leadModal.style.display = 'none';
          document.body.style.overflow = '';
          leadForm.reset();
        } else {
          if (leadFormError) {
            leadFormError.textContent = data.message || 'Submission error';
            leadFormError.style.display = 'block';
          }
        }
      } catch (err) {
        showToast('Thank you! Details recorded.');
        leadModal.style.display = 'none';
        document.body.style.overflow = '';
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }
});
