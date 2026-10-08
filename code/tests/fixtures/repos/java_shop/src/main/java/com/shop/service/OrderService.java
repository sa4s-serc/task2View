package com.shop.service;

import com.shop.domain.*;
import com.shop.repository.OrderRepository;

public class OrderService {
    private OrderRepository repository;
    private PaymentGateway gateway;

    public Order pay(Long id) {
        Order order = repository.findById(id);
        if (order.getStatus() != OrderStatus.NEW) {
            throw new IllegalStateException("not payable");
        }
        gateway.charge(order);
        order.setStatus(OrderStatus.PAID);
        return repository.save(order);
    }
}
