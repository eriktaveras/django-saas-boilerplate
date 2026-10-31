# Stripe Subscription System

A robust and flexible subscription system built with Django and Stripe, designed to handle recurring payments and subscription management for your SaaS application.

## 🌟 Features

- 💳 Secure payment processing with Stripe
- 🔄 Recurring subscription management
- 📊 Subscription status tracking
- 🔔 Webhook integration for real-time updates
- 🎨 Responsive UI with Tailwind CSS
- 🔒 Secure authentication integration
- 📱 Mobile-friendly design

## 🚀 Quick Start

### 1. Stripe Account Setup

1. Create a [Stripe](https://stripe.com) account if you don't have one
2. Navigate to the Stripe Dashboard -> Developers -> API keys
3. Copy your Publishable and Secret keys

### 2. Product Configuration

1. Go to Stripe Dashboard -> Products
2. Create a new product
3. Add a recurring price (e.g., $9.99/month)
4. Copy the Price ID

### 3. Webhook Setup

1. Go to Stripe Dashboard -> Developers -> Webhooks
2. Add endpoint: `https://your-domain.com/subscriptions/webhook/`
3. Select events: `customer.subscription.created`, `customer.subscription.updated`, and `customer.subscription.deleted`
4. Copy the Webhook Signing Secret

### 4. Environment Configuration

Add the following to your `.env` file:
```env
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

## 📁 Module Structure

```
subscriptions/
├── models.py          # Subscription and customer models
├── views.py          # Subscription views and logic
├── urls.py           # URL routing
├── webhooks.py       # Stripe webhook handlers
└── templates/        # Subscription templates
    └── subscription.html
```

## 🔧 Customization

### Subscription Plans
- Modify subscription plans in the Stripe Dashboard
- Update `STRIPE_PRICE_ID` in your `.env` file
- Customize plan features in `models.py`

### UI Customization
- Edit `templates/subscriptions/subscription.html` for UI changes
- Modify styles in your Tailwind CSS configuration
- Add custom JavaScript for enhanced interactivity

### Business Logic
- Extend `views.py` for custom subscription logic
- Modify webhook handlers in `webhooks.py`
- Add custom validation in `models.py`

## 🔒 Security Features

- Environment variable protection for sensitive keys
- Webhook signature verification
- CSRF protection on all forms
- Login-required views
- Secure payment processing
- PCI compliance through Stripe

## 📚 API Reference

### Models
- `Subscription`: Tracks subscription status and details
- `Customer`: Stores customer information and Stripe IDs

### Views
- `subscription_view`: Main subscription page
- `webhook`: Handles Stripe webhook events
- `cancel_subscription`: Manages subscription cancellation

### Webhooks
- `handle_subscription_updated`: Processes subscription updates
- `handle_payment_succeeded`: Handles successful payments
- `handle_payment_failed`: Manages failed payments

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## 📝 License

This module is part of the Django SaaS Boilerplate and is licensed under the MIT License. 