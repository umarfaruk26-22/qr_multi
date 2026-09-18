/**
 * Admin Portal JavaScript
 * Status toggle, delete confirmation, live file preview, sidebar toggle
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Sidebar Toggle & Off-Canvas Drawer Handling
  const menuToggle = document.getElementById('menu-toggle');
  const sidebar = document.querySelector('.admin-sidebar');
  const sidebarBackdrop = document.getElementById('sidebar-backdrop');
  const sidebarCloseBtn = document.getElementById('sidebar-close-btn');

  const openSidebar = () => {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
    document.body.style.overflow = window.innerWidth <= 900 ? 'hidden' : '';
  };

  const closeSidebar = () => {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
    document.body.style.overflow = '';
  };

  // Toggle button on header topbar
  if (menuToggle && sidebar) {
    const handleToggle = (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    };
    menuToggle.addEventListener('click', handleToggle);
    menuToggle.addEventListener('touchend', (e) => {
      handleToggle(e);
    }, { passive: false });
  }

  // Dedicated Close (X) button in sidebar header
  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', (e) => {
      e.preventDefault();
      closeSidebar();
    });
    sidebarCloseBtn.addEventListener('touchend', (e) => {
      e.preventDefault();
      closeSidebar();
    }, { passive: false });
  }

  // Backdrop overlay click & touch handling
  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', (e) => {
      e.preventDefault();
      closeSidebar();
    });
    sidebarBackdrop.addEventListener('touchend', (e) => {
      e.preventDefault();
      closeSidebar();
    }, { passive: false });
  }

  // Close sidebar on navigation click on mobile screens
  document.querySelectorAll('.admin-sidebar .nav-link').forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 900) {
        closeSidebar();
      }
    });
  });

  // Close sidebar on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });

  // Touch Swipe-Left to Close Sidebar Gesture
  if (sidebar) {
    let touchStartX = 0;
    let touchStartY = 0;

    sidebar.addEventListener('touchstart', (e) => {
      if (e.touches && e.touches[0]) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    sidebar.addEventListener('touchend', (e) => {
      if (e.changedTouches && e.changedTouches[0]) {
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        const diffX = touchStartX - touchEndX;
        const diffY = Math.abs(touchStartY - touchEndY);

        // Swipe left threshold: at least 45px left and mainly horizontal
        if (diffX > 45 && diffY < 80 && sidebar.classList.contains('open')) {
          closeSidebar();
        }
      }
    }, { passive: true });
  }

  // Reset scroll lock if window resized to desktop
  window.addEventListener('resize', () => {
    if (window.innerWidth > 900 && sidebar && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });

  // Image Upload Live Preview
  const setupImagePreview = (inputId, previewId, placeholderId) => {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const placeholder = document.getElementById(placeholderId);

    if (input && preview) {
      input.addEventListener('change', function () {
        const file = this.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function (e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
          };
          reader.readAsDataURL(file);
        }
      });
    }
  };

  setupImagePreview('profile_image', 'profile_preview', 'profile_placeholder');
  setupImagePreview('company_logo', 'logo_preview', 'logo_placeholder');

  // AJAX Status Toggle Button
  document.querySelectorAll('.btn-toggle-status').forEach((btn) => {
    btn.addEventListener('click', async function (e) {
      e.preventDefault();
      const empId = this.getAttribute('data-id');
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                        document.querySelector('input[name="csrf_token"]')?.value;

      try {
        const formData = new FormData();
        formData.append('csrf_token', csrfToken);

        const response = await fetch(`/admin/employees/${empId}/toggle-status`, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (data.success) {
          showToast(data.message, 'success');
          // Update badge in table if present
          const badge = document.getElementById(`status-badge-${empId}`);
          if (badge) {
            if (data.is_active === 1) {
              badge.className = 'badge badge-active';
              badge.innerHTML = '<span class="badge-dot"></span> Active';
              this.textContent = 'Deactivate';
            } else {
              badge.className = 'badge badge-inactive';
              badge.innerHTML = '<span class="badge-dot"></span> Inactive';
              this.textContent = 'Activate';
            }
          }
        } else {
          showToast(data.message || 'Failed to update status', 'danger');
        }
      } catch (err) {
        console.error('Error toggling status:', err);
        showToast('Network error while updating status', 'danger');
      }
    });
  });

  // Delete Confirmation Modal Handling
  const deleteModal = document.getElementById('delete-confirm-modal');
  const deleteForm = document.getElementById('delete-employee-form');
  const deleteEmpName = document.getElementById('delete-employee-name');

  document.querySelectorAll('.btn-trigger-delete').forEach((btn) => {
    btn.addEventListener('click', function () {
      const empId = this.getAttribute('data-id');
      const empName = this.getAttribute('data-name');
      if (deleteForm && deleteModal) {
        deleteForm.action = `/admin/employees/${empId}/delete`;
        if (deleteEmpName) deleteEmpName.textContent = empName;
        openModal('delete-confirm-modal');
      }
    });
  });

  // QR Preview Modal Handling
  document.querySelectorAll('.btn-preview-qr').forEach((btn) => {
    btn.addEventListener('click', function () {
      const qrUrl = this.getAttribute('data-qr-img');
      const empName = this.getAttribute('data-name');
      const profileUrl = this.getAttribute('data-profile-url');
      const empId = this.getAttribute('data-id');

      const modalQrImg = document.getElementById('modal-qr-image');
      const modalEmpName = document.getElementById('modal-emp-name');
      const modalProfileLink = document.getElementById('modal-profile-link');
      const btnDownloadPng = document.getElementById('btn-download-png');
      const btnDownloadSvg = document.getElementById('btn-download-svg');
      const btnDownloadBranded = document.getElementById('btn-download-branded');

      if (modalQrImg) modalQrImg.src = qrUrl;
      if (modalEmpName) modalEmpName.textContent = empName;
      if (modalProfileLink) {
        modalProfileLink.href = profileUrl;
        modalProfileLink.textContent = profileUrl;
      }
      if (btnDownloadPng) btnDownloadPng.href = `/admin/qr/download/${empId}/png`;
      if (btnDownloadSvg) btnDownloadSvg.href = `/admin/qr/download/${empId}/svg`;
      if (btnDownloadBranded) btnDownloadBranded.href = `/admin/qr/download/${empId}/branded`;

      openModal('qr-preview-modal');
    });
  });

  // Real-Time Live Preview Sync in Form Builder
  const firstNameInput = document.getElementById('first_name');
  const lastNameInput = document.getElementById('last_name');
  const slugInput = document.getElementById('slug');
  const desigInput = document.getElementById('designation');
  const bioInput = document.getElementById('bio');
  const reviewInput = document.getElementById('google_review_url');
  const whatsappInput = document.getElementById('whatsapp');
  const phoneInput = document.getElementById('phone');
  
  const instagramInput = document.getElementById('instagram_url');
  const linkedinInput = document.getElementById('linkedin_url');
  const facebookInput = document.getElementById('facebook_url');
  const youtubeInput = document.getElementById('youtube_url');
  const websiteInput = document.getElementById('website_url');

  const previewName = document.getElementById('live-preview-name');
  const previewDesig = document.getElementById('live-preview-desig');
  const previewBio = document.getElementById('live-preview-bio');
  const previewAvatarInitials = document.getElementById('live-preview-initials');
  const previewAvatarImg = document.getElementById('live-preview-avatar-img');
  const previewReviewBtn = document.getElementById('live-preview-review-btn');
  const previewWhatsappBtn = document.getElementById('live-preview-whatsapp-btn');
  const previewInstagramBtn = document.getElementById('live-preview-instagram-btn');
  const previewLinkedinBtn = document.getElementById('live-preview-linkedin-btn');
  const previewFacebookBtn = document.getElementById('live-preview-facebook-btn');
  const previewYoutubeBtn = document.getElementById('live-preview-youtube-btn');
  const previewWebsiteBtn = document.getElementById('live-preview-website-btn');
  const slugPreviewText = document.getElementById('live-slug-preview-text');

  const sanitizeSlug = (text) => {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
  };

  const updatePreview = () => {
    const fName = firstNameInput?.value.trim() || '';
    const lName = lastNameInput?.value.trim() || '';
    const fullName = `${fName} ${lName}`.trim();
    
    // Update Name & Initials
    if (previewName) {
      previewName.textContent = fullName || 'Employee Name';
    }
    if (previewAvatarInitials) {
      const init = (fName ? fName[0] : 'E') + (lName ? lName[0] : '');
      previewAvatarInitials.textContent = init.toUpperCase();
    }

    // Update Slug Preview
    if (slugPreviewText) {
      const customSlug = slugInput?.value.trim();
      const currentSlug = customSlug || sanitizeSlug(fName) || 'employee';
      slugPreviewText.textContent = currentSlug;
    }

    // Update Designation
    if (previewDesig) {
      previewDesig.textContent = desigInput?.value.trim() || 'Designation / Role';
    }

    // Update Bio
    if (previewBio) {
      const bioVal = bioInput?.value.trim();
      if (bioVal) {
        previewBio.textContent = bioVal;
        previewBio.style.display = 'block';
      } else {
        previewBio.textContent = 'Welcome to my official digital profile. Connect with me directly!';
        previewBio.style.display = 'block';
      }
    }

    // Toggle Review Button Preview
    if (previewReviewBtn) {
      previewReviewBtn.style.display = reviewInput?.value.trim() ? 'flex' : 'none';
    }

    // Toggle WhatsApp Button Preview
    if (previewWhatsappBtn) {
      previewWhatsappBtn.style.display = (whatsappInput?.value.trim() || phoneInput?.value.trim()) ? 'flex' : 'none';
    }

    // Toggle Social Buttons Preview
    if (previewInstagramBtn) {
      previewInstagramBtn.style.display = instagramInput?.value.trim() ? 'flex' : 'none';
    }
    if (previewLinkedinBtn) {
      previewLinkedinBtn.style.display = linkedinInput?.value.trim() ? 'flex' : 'none';
    }
    if (previewFacebookBtn) {
      previewFacebookBtn.style.display = facebookInput?.value.trim() ? 'flex' : 'none';
    }
    if (previewYoutubeBtn) {
      previewYoutubeBtn.style.display = youtubeInput?.value.trim() ? 'flex' : 'none';
    }
    if (previewWebsiteBtn) {
      previewWebsiteBtn.style.display = websiteInput?.value.trim() ? 'flex' : 'none';
    }
  };

  // Smart Auto-Prefixing for Social Handles
  const setupSmartPrefix = (input, prefixer) => {
    if (!input) return;
    input.addEventListener('blur', function () {
      let val = this.value.trim();
      if (val) {
        const formatted = prefixer(val);
        if (formatted !== val) {
          this.value = formatted;
          updatePreview();
        }
      }
    });
  };

  setupSmartPrefix(instagramInput, (val) => {
    if (!val.startsWith('http://') && !val.startsWith('https://')) {
      const handle = val.replace(/^@/, '').replace(/^instagram\.com\//, '');
      return `https://instagram.com/${handle}`;
    }
    return val;
  });

  setupSmartPrefix(linkedinInput, (val) => {
    if (!val.startsWith('http://') && !val.startsWith('https://')) {
      const handle = val.replace(/^in\//, '').replace(/^linkedin\.com\/in\//, '');
      return `https://linkedin.com/in/${handle}`;
    }
    return val;
  });

  setupSmartPrefix(facebookInput, (val) => {
    if (!val.startsWith('http://') && !val.startsWith('https://')) {
      const handle = val.replace(/^facebook\.com\//, '');
      return `https://facebook.com/${handle}`;
    }
    return val;
  });

  setupSmartPrefix(youtubeInput, (val) => {
    if (!val.startsWith('http://') && !val.startsWith('https://')) {
      let handle = val.replace(/^youtube\.com\//, '');
      if (!handle.startsWith('@') && !handle.startsWith('c/') && !handle.startsWith('channel/')) {
        handle = '@' + handle;
      }
      return `https://youtube.com/${handle}`;
    }
    return val;
  });

  setupSmartPrefix(websiteInput, (val) => {
    if (val && !val.startsWith('http://') && !val.startsWith('https://')) {
      return `https://${val}`;
    }
    return val;
  });

  [firstNameInput, lastNameInput, desigInput, bioInput, reviewInput, whatsappInput, phoneInput, instagramInput, linkedinInput, facebookInput, youtubeInput, websiteInput].forEach(input => {
    if (input) {
      input.addEventListener('input', updatePreview);
    }
  });

  if (slugInput) {
    slugInput.addEventListener('input', () => {
      if (slugPreviewText) {
        slugPreviewText.textContent = slugInput.value.trim() || sanitizeSlug(firstNameInput?.value || '') || 'employee';
      }
    });
  }

  // Sync uploaded photo with live preview avatar
  const profileImageInput = document.getElementById('profile_image');
  if (profileImageInput && previewAvatarImg && previewAvatarInitials) {
    profileImageInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          previewAvatarImg.src = e.target.result;
          previewAvatarImg.style.display = 'block';
          previewAvatarInitials.style.display = 'none';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // ==========================================================================
  // Dynamic Custom Channel & Social Links Builder Engine
  // ==========================================================================
  const customLinksContainer = document.getElementById('custom-links-container');
  const btnAddCustomLink = document.getElementById('btn-add-custom-link');
  const emptyStateNotice = document.getElementById('custom-links-empty-state');
  const previewCustomLinksContainer = document.getElementById('live-preview-custom-links-container');

  const PLATFORMS_CONFIG = {
    twitter: {
      title: 'Twitter / X',
      placeholder: 'https://x.com/username',
      badgeClass: 'badge-twitter',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'
    },
    telegram: {
      title: 'Telegram',
      placeholder: 'https://t.me/username',
      badgeClass: 'badge-telegram',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>'
    },
    messenger: {
      title: 'Messenger',
      placeholder: 'https://m.me/username',
      badgeClass: 'badge-messenger',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.373 0 0 4.974 0 11.111c0 3.498 1.744 6.614 4.469 8.654V24l4.088-2.242c1.077.299 2.222.463 3.443.463 6.627 0 12-4.975 12-11.11S18.627 0 12 0zm1.191 14.963l-3.055-3.26-5.964 3.26 6.559-6.963 3.13 3.259 5.889-3.259-6.559 6.963z"/></svg>'
    },
    github: {
      title: 'GitHub',
      placeholder: 'https://github.com/username',
      badgeClass: 'badge-github',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>'
    },
    discord: {
      title: 'Discord',
      placeholder: 'https://discord.gg/invite',
      badgeClass: 'badge-discord',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>'
    },
    calendly: {
      title: 'Schedule Meeting',
      placeholder: 'https://calendly.com/your-calendar',
      badgeClass: 'badge-calendly',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
    },
    behance: {
      title: 'Behance Portfolio',
      placeholder: 'https://behance.net/username',
      badgeClass: 'badge-behance',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-4.726 3-3.341 0-5.834-2.261-5.834-5.908 0-3.486 2.368-6.092 5.76-6.092 3.398 0 5.405 2.463 5.405 5.922 0 .428-.046.856-.091 1.078h-8.232c.105 1.579 1.364 2.825 3.064 2.825 1.352 0 2.213-.647 2.684-1.325h1.97zm-5.011-4.225c-.092-1.282-1.066-2.162-2.387-2.162-1.35 0-2.316.91-2.484 2.162h4.871zm-13.715-7.775h5.482c2.094 0 3.518.91 3.518 2.646 0 1.157-.614 2.067-1.636 2.417 1.356.37 2.136 1.492 2.136 2.879 0 2.083-1.652 3.058-3.87 3.058h-5.63v-11zm2.741 4.542h2.247c.854 0 1.411-.424 1.411-1.127 0-.756-.566-1.156-1.411-1.156h-2.247v2.283zm0 4.195h2.464c.949 0 1.554-.484 1.554-1.289 0-.847-.645-1.267-1.639-1.267h-2.379v2.556z"/></svg>'
    },
    spotify: {
      title: 'Spotify / Music',
      placeholder: 'https://open.spotify.com/user/username',
      badgeClass: 'badge-spotify',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.49 17.307a.755.755 0 0 1-1.04.249c-2.85-1.741-6.438-2.135-10.665-1.169a.755.755 0 0 1-.336-1.472c4.629-1.057 8.59-.611 11.792 1.352.36.221.472.688.249 1.04zm1.464-3.256a.945.945 0 0 1-1.301.311c-3.263-2.006-8.238-2.587-12.098-1.415a.946.946 0 0 1-.557-1.808c4.412-1.339 9.897-.692 13.645 1.611a.946.946 0 0 1 .311 1.301zm.126-3.393c-3.914-2.324-10.364-2.538-14.095-1.405a1.133 1.133 0 1 1-.659-2.171c4.288-1.302 11.41-1.05 15.918 1.626a1.134 1.134 0 0 1-1.164 1.95z"/></svg>'
    },
    pinterest: {
      title: 'Pinterest',
      placeholder: 'https://pinterest.com/username',
      badgeClass: 'badge-pinterest',
      svg: '<svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0a12 12 0 0 0-4.37 23.18c-.03-.97-.05-2.47.1-3.53l1.1-4.68s-.28-.56-.28-1.38c0-1.29.75-2.26 1.68-2.26.79 0 1.17.6 1.17 1.31 0 .8-.51 1.99-.77 3.1-.22.93.47 1.68 1.38 1.68 1.66 0 2.94-1.75 2.94-4.27 0-2.23-1.6-3.79-3.9-3.79-2.66 0-4.22 2-4.22 4.06 0 .8.31 1.67.7 2.14.08.1.09.18.07.28l-.26 1.07c-.04.18-.14.22-.32.13-1.2-.56-1.95-2.31-1.95-3.72 0-3.03 2.2-5.81 6.35-5.81 3.33 0 5.92 2.38 5.92 5.55 0 3.31-2.09 5.98-4.99 5.98-.97 0-1.89-.51-2.2-.1.11l-.6 2.28c-.22.84-.81 1.89-1.21 2.53A12 12 0 1 0 12 0z"/></svg>'
    },
    custom: {
      title: 'Custom Link',
      placeholder: 'https://your-custom-link.com',
      badgeClass: 'badge-custom',
      svg: '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line></svg>'
    }
  };

  const updateCustomLinksLivePreview = () => {
    if (!previewCustomLinksContainer) return;
    previewCustomLinksContainer.innerHTML = '';

    const rows = customLinksContainer ? customLinksContainer.querySelectorAll('.custom-link-row') : [];
    if (emptyStateNotice) {
      emptyStateNotice.style.display = rows.length === 0 ? 'block' : 'none';
    }

    rows.forEach(row => {
      const platformSelect = row.querySelector('.custom-platform-select');
      const titleInput = row.querySelector('.custom-title-input');
      const urlInput = row.querySelector('.custom-url-input');

      const plat = platformSelect?.value || 'custom';
      const conf = PLATFORMS_CONFIG[plat] || PLATFORMS_CONFIG.custom;
      const title = titleInput?.value.trim() || conf.title;
      const url = urlInput?.value.trim();

      if (url) {
        const miniBtn = document.createElement('div');
        miniBtn.className = 'mini-btn-social';
        miniBtn.style.display = 'flex';
        miniBtn.style.alignItems = 'center';
        miniBtn.style.justifyContent = 'space-between';
        miniBtn.style.padding = '7px 10px';
        miniBtn.style.borderRadius = '8px';
        miniBtn.style.background = 'rgba(255, 255, 255, 0.06)';
        miniBtn.style.border = '1px solid rgba(255, 255, 255, 0.08)';
        miniBtn.style.color = '#f1f5f9';
        miniBtn.style.fontSize = '0.73rem';
        miniBtn.style.fontWeight = '600';

        miniBtn.innerHTML = `
          <div style="display: flex; align-items: center; gap: 6px;">
            <span class="mini-social-badge ${conf.badgeClass}">
              ${conf.svg}
            </span>
            <span>${escapeHtml(title)}</span>
          </div>
          <span>→</span>
        `;
        previewCustomLinksContainer.appendChild(miniBtn);
      }
    });
  };

  const attachRowEvents = (row) => {
    const platformSelect = row.querySelector('.custom-platform-select');
    const titleInput = row.querySelector('.custom-title-input');
    const urlInput = row.querySelector('.custom-url-input');
    const removeBtn = row.querySelector('.btn-remove-custom-link');

    if (platformSelect) {
      platformSelect.addEventListener('change', function () {
        const conf = PLATFORMS_CONFIG[this.value] || PLATFORMS_CONFIG.custom;
        if (titleInput && (!titleInput.value || Object.values(PLATFORMS_CONFIG).some(c => c.title === titleInput.value))) {
          titleInput.value = conf.title;
        }
        if (urlInput) {
          urlInput.placeholder = conf.placeholder;
        }
        updateCustomLinksLivePreview();
      });
    }

    if (titleInput) {
      titleInput.addEventListener('input', updateCustomLinksLivePreview);
    }

    if (urlInput) {
      urlInput.addEventListener('input', updateCustomLinksLivePreview);
      
      // Smart Auto Prefixing on Blur
      urlInput.addEventListener('blur', function () {
        let val = this.value.trim();
        const plat = platformSelect ? platformSelect.value : 'custom';
        if (val && !val.startsWith('http://') && !val.startsWith('https://')) {
          if (plat === 'twitter') {
            const handle = val.replace(/^@/, '').replace(/^x\.com\//, '').replace(/^twitter\.com\//, '');
            this.value = `https://x.com/${handle}`;
          } else if (plat === 'telegram') {
            const handle = val.replace(/^@/, '').replace(/^t\.me\//, '');
            this.value = `https://t.me/${handle}`;
          } else if (plat === 'messenger') {
            const handle = val.replace(/^m\.me\//, '');
            this.value = `https://m.me/${handle}`;
          } else if (plat === 'github') {
            const handle = val.replace(/^@/, '').replace(/^github\.com\//, '');
            this.value = `https://github.com/${handle}`;
          } else if (plat === 'calendly') {
            const handle = val.replace(/^calendly\.com\//, '');
            this.value = `https://calendly.com/${handle}`;
          } else {
            this.value = `https://${val}`;
          }
          updateCustomLinksLivePreview();
        }
      });
    }

    if (removeBtn) {
      removeBtn.addEventListener('click', function () {
        row.style.opacity = '0';
        row.style.transform = 'translateY(-6px)';
        setTimeout(() => {
          row.remove();
          updateCustomLinksLivePreview();
        }, 150);
      });
    }
  };

  // Create & Append New Dynamic Row
  const createNewCustomLinkRow = (platform = 'twitter', title = '', url = '') => {
    if (!customLinksContainer) return;
    const conf = PLATFORMS_CONFIG[platform] || PLATFORMS_CONFIG.custom;
    const row = document.createElement('div');
    row.className = 'custom-link-row';

    row.innerHTML = `
      <div class="custom-link-row-grid">
        <div class="custom-link-field platform-field">
          <label class="custom-link-field-label">Platform</label>
          <select name="custom_platform[]" class="form-select custom-platform-select">
            <option value="twitter" ${platform === 'twitter' ? 'selected' : ''}>𝕏 Twitter / X</option>
            <option value="telegram" ${platform === 'telegram' ? 'selected' : ''}>✈️ Telegram</option>
            <option value="messenger" ${platform === 'messenger' ? 'selected' : ''}>💬 Messenger</option>
            <option value="github" ${platform === 'github' ? 'selected' : ''}>🐙 GitHub</option>
            <option value="discord" ${platform === 'discord' ? 'selected' : ''}>👾 Discord</option>
            <option value="calendly" ${platform === 'calendly' ? 'selected' : ''}>📅 Calendly (Schedule)</option>
            <option value="behance" ${platform === 'behance' ? 'selected' : ''}>🎨 Behance Portfolio</option>
            <option value="spotify" ${platform === 'spotify' ? 'selected' : ''}>🎵 Spotify / Music</option>
            <option value="pinterest" ${platform === 'pinterest' ? 'selected' : ''}>📌 Pinterest</option>
            <option value="custom" ${platform === 'custom' ? 'selected' : ''}>🌐 Custom Link</option>
          </select>
        </div>
        <div class="custom-link-field title-field">
          <label class="custom-link-field-label">Display Title</label>
          <input type="text" name="custom_title[]" class="form-input custom-title-input" placeholder="Display Title" value="${escapeHtml(title || conf.title)}">
        </div>
        <div class="custom-link-field url-field">
          <label class="custom-link-field-label">Destination URL</label>
          <input type="url" name="custom_url[]" class="form-input custom-url-input" placeholder="${conf.placeholder}" value="${escapeHtml(url)}" required>
        </div>
        <div class="custom-link-field delete-field">
          <label class="custom-link-field-label">&nbsp;</label>
          <button type="button" class="btn-remove-custom-link" title="Remove Link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      </div>
    `;

    customLinksContainer.appendChild(row);
    attachRowEvents(row);
    updateCustomLinksLivePreview();
    row.querySelector('.custom-url-input')?.focus();
  };

  if (btnAddCustomLink) {
    btnAddCustomLink.addEventListener('click', () => {
      createNewCustomLinkRow('twitter', '', '');
    });
  }

  // Initialize existing rows in DOM (e.g. edit page)
  if (customLinksContainer) {
    customLinksContainer.querySelectorAll('.custom-link-row').forEach(attachRowEvents);
    updateCustomLinksLivePreview();
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

