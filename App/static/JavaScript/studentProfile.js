document.addEventListener('DOMContentLoaded', function() {
    // Profile picture upload
    const profilePicInput = document.getElementById('profile-pic-input');
    const profilePicForm = document.getElementById('profile-pic-form');
    const profilePicEditBtn = document.getElementById('profile-pic-edit');
    
    if (profilePicEditBtn) {
      profilePicEditBtn.addEventListener('click', function(e) {
        e.preventDefault();
        profilePicInput.click();
      });
    }
    
    if (profilePicInput) {
      profilePicInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
          profilePicForm.submit();
        }
      });
    }
    
    // Personal info modal
    const personalInfoModal = document.getElementById('personalInfoModal');
    const personalInfoEditBtn = document.getElementById('personal-info-edit');
    const closeModalBtn = document.getElementsByClassName('close')[0];
    
    if (personalInfoEditBtn) {
      personalInfoEditBtn.addEventListener('click', function(e) {
        e.preventDefault();
        personalInfoModal.style.display = 'block';
      });
    }
    
    if (closeModalBtn) {
      closeModalBtn.addEventListener('click', function() {
        personalInfoModal.style.display = 'none';
      });
    }
    
    // Close modal on outside click
    window.addEventListener('click', function(event) {
      if (event.target == personalInfoModal) {
        personalInfoModal.style.display = 'none';
      }
    });
    
    // Cancel button
    const cancelBtn = document.getElementById('cancel-edit');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', function() {
        personalInfoModal.style.display = 'none';
      });
    }
  });