package com.shop.domain;

@Entity
@Table(name = "orders")
public class Order {
    public static final int MAX_ITEMS = 50;
    @Id
    private Long id;
    private OrderStatus status;
    @ManyToOne
    @JoinColumn(name = "customer_id")
    private Customer customer;
    @Transient
    private String cachedLabel;

    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus status) { this.status = status; }
}
