import pytest
from app.core.metrics_engine import (
    calculate_loc,
    parse_and_extract_metrics,
)

SAMPLE_JAVA_SOURCE = """package com.test;

import java.math.BigDecimal;
import java.util.List;

// Sample service for test
public class SampleService {
    private String name;
    private int counter;

    public SampleService(String name) {
        this.name = name;
        this.counter = 0;
    }

    /* Multi-line
       comment */
    public boolean process(int val, BigDecimal amount) {
        if (val > 10 && amount != null) {
            for (int i = 0; i < val; i++) {
                if (i % 2 == 0) {
                    this.counter++;
                }
            }
            return true;
        } else {
            return false;
        }
    }
}
"""


def test_calculate_loc():
    loc = calculate_loc(SAMPLE_JAVA_SOURCE)
    assert loc > 10
    assert loc < 30


def test_parse_and_extract_metrics():
    tree, metrics_dict = parse_and_extract_metrics(SAMPLE_JAVA_SOURCE, "SampleService.java")
    assert tree is not None
    assert "SampleService" in metrics_dict

    m = metrics_dict["SampleService"]
    assert m.loc > 10
    # CC should count: if (1), && (1), for (1), if (1) + base 1 = 5
    assert m.cc >= 4
    assert m.wmc >= 5
    assert m.cbo >= 1  # BigDecimal
    assert 0.0 <= m.lcom <= 1.0
