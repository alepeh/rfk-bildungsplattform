import os
def test_system(request):
    return {
        'TEST_SYSTEM': os.getenv('TEST_SYSTEM', False)
    }