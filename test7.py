import sys
import os

sys.path.append(os.path.abspath("backend"))

from backend.app.modules.module7.service import process_context  # adjust name


def test_module7():
    base_bias = 0.2
    context_bias = 0.4
    dominant_feature = "income"

    result = process_context(base_bias, context_bias, dominant_feature)

    print(result)

test_module7()