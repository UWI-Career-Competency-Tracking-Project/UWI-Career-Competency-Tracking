document.getElementById('resume-input').addEventListener('change', function() {
    if (this.files && this.files[0]) {
      document.getElementById('resume-form').submit();
    }
  });