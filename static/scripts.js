document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('category-select');
    const subcategorySelect = document.getElementById('subcat-select');
    const productSelect = document.getElementById('product-select');
    const topNSlider = document.getElementById('top-n-slider');

    // Helper function to populate a dropdown
    function populateDropdown(dropdownElement, options, selectedValue) {
        dropdownElement.innerHTML = ''; // Clear existing options
        options.forEach(optionText => {
            const option = document.createElement('option');
            option.value = optionText;
            option.textContent = optionText;
            if (optionText === selectedValue) {
                option.selected = true; // Retain selection if applicable
            }
            dropdownElement.appendChild(option);
        });
    }

    // --- Functions for cascading DOWNWARDS (Category -> Subcategory -> Product) ---

    // Function to update subcategories and products based on category selection
    async function updateSubcategoriesAndProducts() {
        const selectedCategory = categorySelect.value;
        
        if (selectedCategory === 'All') {
            // If 'All' category is selected, reset subcategory and product to 'All'
            populateDropdown(subcategorySelect, ['All'].concat(allSubcategories), 'All');
            populateDropdown(productSelect, ['All'].concat(allProducts), 'All');
            return;
        }

        try {
            const response = await fetch('/_get_subcategories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `category=${encodeURIComponent(selectedCategory)}`
            });
            const data = await response.json();
            populateDropdown(subcategorySelect, data.subcategories, 'All'); // Default to 'All' or existing subcategory if valid
            updateProducts(); // Update products based on the new subcategory list
        } catch (error) {
            console.error('Error fetching subcategories:', error);
        }
    }

    // Function to update products based on category and subcategory selection
    async function updateProducts() {
        const selectedCategory = categorySelect.value;
        const selectedSubcategory = subcategorySelect.value;

        if (selectedCategory === 'All' && selectedSubcategory === 'All') {
            populateDropdown(productSelect, ['All'].concat(allProducts), 'All');
            return;
        }

        try {
            const response = await fetch('/_get_products', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `category=${encodeURIComponent(selectedCategory)}&subcategory=${encodeURIComponent(selectedSubcategory)}`
            });
            const data = await response.json();
            populateDropdown(productSelect, data.products, 'All'); // Default to 'All' or existing product if valid
        } catch (error) {
            console.error('Error fetching products:', error);
        }
    }

    // --- Functions for cascading UPWARDS (Product -> Subcategory -> Category) ---

    async function updateParentsFromProduct() {
        const selectedProduct = productSelect.value;

        if (selectedProduct === 'All' || selectedProduct === 'No Products') {
            // If 'All' product, trigger normal cascading down from Category 'All'
            categorySelect.value = 'All'; // Set category to 'All'
            await updateSubcategoriesAndProducts(); // This will reset subcat/product
            return;
        }
        
        try {
            const response = await fetch('/_get_parent_details_for_product', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `product=${encodeURIComponent(selectedProduct)}`
            });
            const data = await response.json();
            
            // Set Category
            categorySelect.value = data.category;
            
            // Fetch and set Subcategory options
            const subcatResponse = await fetch('/_get_subcategories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `category=${encodeURIComponent(data.category)}`
            });
            const subcatData = await subcatResponse.json();
            populateDropdown(subcategorySelect, subcatData.subcategories, data.subcategory);

        } catch (error) {
            console.error('Error fetching parent details for product:', error);
        }
    }

    async function updateParentFromSubcategory() {
        const selectedSubcategory = subcategorySelect.value;

        if (selectedSubcategory === 'All') {
            // If 'All' subcategory, reset product and make sure category is 'All'
            categorySelect.value = 'All'; // Reset category to 'All'
            await updateSubcategoriesAndProducts(); // This will update products as well
            return;
        }

        try {
            const response = await fetch('/_get_parent_category', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `subcategory=${encodeURIComponent(selectedSubcategory)}`
            });
            const data = await response.json();
            
            // Set Category
            categorySelect.value = data.parent_category;
            
            // Update products based on the newly selected category and subcategory
            await updateProducts();

        } catch (error) {
            console.error('Error fetching parent category for subcategory:', error);
        }
    }


    // --- Event Listeners ---
    categorySelect.addEventListener('change', updateSubcategoriesAndProducts);
    subcategorySelect.addEventListener('change', updateParentFromSubcategory);
    productSelect.addEventListener('change', updateParentsFromProduct);

    // --- Initial Load Logic ---
    // This ensures the dropdowns are correctly chained based on the initial state
    if (initialSelectedProduct && initialSelectedProduct !== 'All' && initialSelectedProduct !== 'No Products') {
        productSelect.value = initialSelectedProduct;
        updateParentsFromProduct();
    } else if (initialSelectedSubcategory && initialSelectedSubcategory !== 'All') {
        subcategorySelect.value = initialSelectedSubcategory;
        updateParentFromSubcategory();
    } else {
        updateSubcategoriesAndProducts();
    }


    // Function to apply filters and refresh charts (this will trigger a full page reload)
    window.applyFilters = function() { // Made global to be callable from onclick in HTML
        const category = categorySelect.value;
        const subcat = subcategorySelect.value;
        const product = productSelect.value;
        const top_n = topNSlider.value;

        // Construct the URL with current filter parameters and navigate
        window.location.href = `${storeForecastUrl}?category=${encodeURIComponent(category)}&subcat=${encodeURIComponent(subcat)}&product=${encodeURIComponent(product)}&top_n=${encodeURIComponent(top_n)}`;
    }
});