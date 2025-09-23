                document.addEventListener('DOMContentLoaded', function() {
                    generateBarcode('{{ object.id }}', '{{ object|class_name }}');
                });

                function generateBarcode(objectId, objectType) {
                    fetch('{% url "core:generate_barcode" %}', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        },
                        body: JSON.stringify({
                            'object_id': objectId,
                            'object_type': objectType
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const container = document.querySelector('.barcode-placeholder').parentElement;
                            container.innerHTML = `
                                <img src="${data.barcode_data}" alt="{% trans 'Document Barcode' %}" class="barcode-image">
                                <div class="barcode-info">
                                    <small class="text-muted">${data.serial_number || '{% trans "Scan to access record" %}'}</small>
                                </div>
                            `;
                        }
                    })
                    .catch(error => {
                        console.error('Barcode generation error:', error);
                    });
                }
