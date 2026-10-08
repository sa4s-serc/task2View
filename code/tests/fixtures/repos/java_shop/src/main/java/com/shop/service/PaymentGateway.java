package com.shop.service;

import com.shop.domain.Order;

public interface PaymentGateway {
    void charge(Order order);
}
