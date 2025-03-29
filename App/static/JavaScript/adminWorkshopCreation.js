$(document).ready(function() {
    initializeSelect2();
    
    function initializeSelect2() {
        $('.competencies-select').select2({
            placeholder: 'Select competencies that students will gain from this workshop',
            allowClear: false,
            width: '100%',
            theme: 'default',
            closeOnSelect: false,
            maximumSelectionLength: 20,
            minimumResultsForSearch: 0,
            dropdownParent: null,
            templateResult: formatOption,
            templateSelection: formatSelection,
            matcher: hidingMatcher
        });
    }
    
    function hidingMatcher(params, data) {
        if ($.trim(params.term) === '' && !data.id) {
            return data;
        }

        const selectedValues = $('.competencies-select').val() || [];
        
        if (selectedValues.includes(data.id)) {
            return null;
        }

        if (params.term && params.term.trim() !== '') {
            const original = data.text.toUpperCase();
            const term = params.term.toUpperCase();
            
            if (original.indexOf(term) > -1) {
                return data;
            }
            
            return null;
        }

        return data;
    }
    
    function formatOption(option) {
        if (!option.id) return option.text;
        
        const selectedValues = $('.competencies-select').val() || [];
        const isSelected = selectedValues.includes(option.id);
        
        if (isSelected) return null;
         
        const $option = $(
            '<div class="select-option">' +
                '<div class="select-option-text">' + option.text + '</div>' +
            '</div>'
        );
        
        return $option;
    }
    
    function formatSelection(option) {
        if (!option.id) return option.text;
        return $('<span>' + option.text + '</span>');
    }
    
    function refreshDropdown() {
        const select = $('.competencies-select');
        
        select.select2('close');
        setTimeout(() => {
            select.select2('open');
        }, 0);
    }
    
    function addHelperText() {
        const dropdown = document.querySelector('.select2-dropdown');
        if (!dropdown) return;
        
        let helpText = dropdown.querySelector('.select2-help-text');
        
        if (!helpText) {
            helpText = document.createElement('div');
            helpText.className = 'select2-help-text';
            helpText.textContent = 'Click on items to add them to your selection';
            dropdown.appendChild(helpText);
        }
    }
    
    $('.competencies-select').on('select2:open', function() {
        setTimeout(function() {
            const dropdown = $('.select2-dropdown');
            if (dropdown.length) {
                dropdown.css({
                    'z-index': 9999,
                    'opacity': 1,
                    'visibility': 'visible'
                });
            }
            
            addHelperText();
        }, 10);
    });
    
    $('.competencies-select').on('select2:unselect', function(e) {
        refreshDropdown();
    });
    
    $(document).on('mousedown', '.select2-results__option', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const option = $(this).data('data');
        if (!option || !option.id) return;
        
        const select = $('.competencies-select');
        const selectedValues = select.val() || [];
        
        const newValues = [...selectedValues, option.id];
        
        select.val(newValues).trigger('change');
        
        refreshDropdown();
        
        return false;
    });

    $('.competencies-select').on('change', function(e) {
        if ($('.select2-container--open').length) {
            refreshDropdown();
        }
    });
    
    window.addEventListener('load', function() {
        const loader = document.getElementById('loader');
        if (loader) {
            setTimeout(function() {
                loader.style.opacity = "0";
                setTimeout(function() {
                    loader.style.display = "none";
                }, 500);
            }, 1000);
        }
    });
}); 