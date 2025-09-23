// Alpine.js Test Verification
// Run this in browser console on patient list page to verify Alpine.js is working

console.log('🧪 Testing Alpine.js Integration...');

// Test 1: Check if Alpine.js is loaded
if (typeof Alpine !== 'undefined') {
    console.log('✅ Alpine.js is loaded (version:', Alpine.version || 'unknown', ')');
} else {
    console.log('❌ Alpine.js is NOT loaded');
}

// Test 2: Check if patient manager is initialized
const patientContainer = document.querySelector('[x-data="patientManager()"]');
if (patientContainer) {
    console.log('✅ Patient manager Alpine component found');

    // Test 3: Check if Alpine data is accessible
    if (patientContainer._x_dataStack) {
        console.log('✅ Alpine data stack is initialized');
        const data = patientContainer._x_dataStack[0];
        console.log('📊 Current Alpine state:', {
            searchQuery: data.searchQuery,
            selectedPatients: data.selectedPatients,
            showDeleteModal: data.showDeleteModal
        });
    } else {
        console.log('❌ Alpine data stack not found');
    }
} else {
    console.log('❌ Patient manager Alpine component not found');
}

// Test 4: Check HTMX integration
if (typeof htmx !== 'undefined') {
    console.log('✅ HTMX is loaded (version:', htmx.version || 'unknown', ')');
} else {
    console.log('❌ HTMX is NOT loaded');
}

console.log('🎯 Alpine.js + HTMX Integration Test Complete');
