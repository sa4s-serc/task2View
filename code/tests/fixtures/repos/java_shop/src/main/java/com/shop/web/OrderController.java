package com.shop.web;

import com.shop.service.OrderService;
import com.shop.domain.Order;

@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) { this.orderService = orderService; }

    @PostMapping("/{id}/pay")
    public Order pay(Long id) {
        return orderService.pay(id);
    }
}
