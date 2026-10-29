import os
import shutil
import logging
from pathlib import Path
import git

logger = logging.getLogger("software_dna.mock_repo")

MOCK_REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "generated" / "mock_repo"

# Helper Java classes that support the architecture
PAYMENT_REQUEST_JAVA = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class PaymentRequest {
    private String transactionId;
    private String accountId;
    private BigDecimal amount;
    private String currency;
    private String paymentMethod;
    private String cardToken;
    private String ipAddress;
    private String merchantId;

    public PaymentRequest(String transactionId, String accountId, BigDecimal amount, String currency, String paymentMethod) {
        this.transactionId = transactionId;
        this.accountId = accountId;
        this.amount = amount;
        this.currency = currency;
        this.paymentMethod = paymentMethod;
    }

    public String getTransactionId() { return transactionId; }
    public String getAccountId() { return accountId; }
    public BigDecimal getAmount() { return amount; }
    public String getCurrency() { return currency; }
    public String getPaymentMethod() { return paymentMethod; }
    public String getCardToken() { return cardToken; }
    public void setCardToken(String token) { this.cardToken = token; }
    public String getIpAddress() { return ipAddress; }
    public void setIpAddress(String ip) { this.ipAddress = ip; }
    public String getMerchantId() { return merchantId; }
    public void setMerchantId(String id) { this.merchantId = id; }
}
"""

PAYMENT_RESPONSE_JAVA = """package com.evolutionary.payment;

public class PaymentResponse {
    private String transactionId;
    private String status;
    private String authorizationCode;
    private String errorMessage;
    private long timestamp;

    public PaymentResponse(String transactionId, String status, String authorizationCode) {
        this.transactionId = transactionId;
        this.status = status;
        this.authorizationCode = authorizationCode;
        this.timestamp = System.currentTimeMillis();
    }

    public String getTransactionId() { return transactionId; }
    public String getStatus() { return status; }
    public String getAuthorizationCode() { return authorizationCode; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String msg) { this.errorMessage = msg; }
    public long getTimestamp() { return timestamp; }
}
"""

PAYMENT_GATEWAY_JAVA = """package com.evolutionary.payment;

public class PaymentGateway {
    public boolean authorize(PaymentRequest request) {
        return request != null && request.getAmount() != null;
    }

    public boolean capture(String transactionId) {
        return transactionId != null && !transactionId.isEmpty();
    }

    public boolean refund(String transactionId) {
        return transactionId != null;
    }
}
"""

NOTIFICATION_SERVICE_JAVA = """package com.evolutionary.payment;

public class NotificationService {
    public void sendReceipt(PaymentRequest request, PaymentResponse response) {
        if (request != null && response != null) {
            System.out.println("Receipt dispatched for: " + request.getTransactionId());
        }
    }

    public void sendAlert(String message, String severity) {
        System.err.println("[" + severity + "] Notification Alert: " + message);
    }
}
"""

AUDIT_LOGGER_JAVA = """package com.evolutionary.payment;

public class AuditLogger {
    public void logTransaction(String txId, String status, String details) {
        System.out.println("[AUDIT] Tx: " + txId + " | Status: " + status + " | Details: " + details);
    }

    public void logSecurityEvent(String eventType, String accountId, String ip) {
        System.out.println("[SECURITY] " + eventType + " from " + ip + " for account " + accountId);
    }
}
"""

FRAUD_DETECTION_JAVA = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class FraudDetectionClient {
    public boolean evaluateRisk(String accountId, BigDecimal amount, String ipAddress) {
        if (amount != null && amount.compareTo(new BigDecimal("10000")) > 0) {
            return false;
        }
        return ipAddress != null && !ipAddress.startsWith("192.168.0.");
    }
}
"""

CURRENCY_CONVERTER_JAVA = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class CurrencyConverter {
    public BigDecimal convert(BigDecimal amount, String sourceCurrency, String targetCurrency) {
        if (sourceCurrency != null && sourceCurrency.equalsIgnoreCase(targetCurrency)) {
            return amount;
        }
        return amount != null ? amount.multiply(new BigDecimal("1.10")) : BigDecimal.ZERO;
    }
}
"""

TAX_SERVICE_JAVA = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class TaxService {
    public BigDecimal calculateTax(BigDecimal amount, String jurisdiction) {
        if ("EU".equalsIgnoreCase(jurisdiction)) {
            return amount.multiply(new BigDecimal("0.20"));
        } else if ("US".equalsIgnoreCase(jurisdiction)) {
            return amount.multiply(new BigDecimal("0.08"));
        }
        return BigDecimal.ZERO;
    }
}
"""

TOKEN_VAULT_JAVA = """package com.evolutionary.payment;

public class TokenVault {
    public String tokenize(String rawCard) {
        if (rawCard == null || rawCard.length() < 12) {
            return "INVALID_TOKEN";
        }
        return "TKN-" + rawCard.hashCode();
    }

    public boolean validateToken(String token) {
        return token != null && token.startsWith("TKN-");
    }
}
"""

LEDGER_SYNC_JAVA = """package com.evolutionary.payment;

public class LedgerSyncService {
    public void recordEntry(String accountId, String type, String amountStr) {
        System.out.println("[LEDGER] " + accountId + " " + type + " " + amountStr);
    }
}
"""

# V1 PaymentService: Clean, modular, well-proportioned
PAYMENT_SERVICE_V1 = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class PaymentService {
    private final PaymentGateway gateway;
    private final NotificationService notifier;
    private final AuditLogger logger;

    public PaymentService(PaymentGateway gateway, NotificationService notifier, AuditLogger logger) {
        this.gateway = gateway;
        this.notifier = notifier;
        this.logger = logger;
    }

    public PaymentResponse processPayment(PaymentRequest request) {
        if (request == null) {
            return new PaymentResponse(null, "FAILED", null);
        }

        if (request.getAmount() == null || request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            logger.logTransaction(request.getTransactionId(), "INVALID", "Non-positive amount");
            return new PaymentResponse(request.getTransactionId(), "FAILED", null);
        }

        boolean authorized = gateway.authorize(request);
        if (authorized) {
            gateway.capture(request.getTransactionId());
            PaymentResponse response = new PaymentResponse(request.getTransactionId(), "SUCCESS", "AUTH-" + System.currentTimeMillis());
            notifier.sendReceipt(request, response);
            logger.logTransaction(request.getTransactionId(), "SUCCESS", "Authorized and captured");
            return response;
        } else {
            logger.logTransaction(request.getTransactionId(), "DECLINED", "Gateway rejected");
            return new PaymentResponse(request.getTransactionId(), "DECLINED", null);
        }
    }
}
"""

# V2 PaymentService: Validation features added
PAYMENT_SERVICE_V2 = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class PaymentService {
    private final PaymentGateway gateway;
    private final NotificationService notifier;
    private final AuditLogger logger;

    public PaymentService(PaymentGateway gateway, NotificationService notifier, AuditLogger logger) {
        this.gateway = gateway;
        this.notifier = notifier;
        this.logger = logger;
    }

    public PaymentResponse processPayment(PaymentRequest request) {
        if (request == null) {
            return new PaymentResponse(null, "FAILED", null);
        }

        if (request.getAccountId() == null || request.getAccountId().trim().isEmpty()) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Missing account ID");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_MISSING_ACCOUNT", null);
        }

        if (request.getCurrency() == null || request.getCurrency().length() != 3) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Invalid ISO currency");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_INVALID_CURRENCY", null);
        }

        if (request.getAmount() == null || request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            logger.logTransaction(request.getTransactionId(), "INVALID", "Non-positive amount");
            return new PaymentResponse(request.getTransactionId(), "FAILED_INVALID_AMOUNT", null);
        }

        if (request.getPaymentMethod() == null) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Null method");
            return new PaymentResponse(request.getTransactionId(), "FAILED_MISSING_METHOD", null);
        }

        boolean authorized = gateway.authorize(request);
        if (authorized) {
            gateway.capture(request.getTransactionId());
            PaymentResponse response = new PaymentResponse(request.getTransactionId(), "SUCCESS", "AUTH-" + System.currentTimeMillis());
            notifier.sendReceipt(request, response);
            logger.logTransaction(request.getTransactionId(), "SUCCESS", "Authorized and captured");
            return response;
        } else {
            logger.logTransaction(request.getTransactionId(), "DECLINED", "Gateway rejected");
            return new PaymentResponse(request.getTransactionId(), "DECLINED", null);
        }
    }
}
"""

# V3 PaymentService: Retry logic, circuit breaker, exponential backoff, fraud check debt
PAYMENT_SERVICE_V3 = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class PaymentService {
    private final PaymentGateway gateway;
    private final NotificationService notifier;
    private final AuditLogger logger;
    private final FraudDetectionClient fraudClient;

    public PaymentService(PaymentGateway gateway, NotificationService notifier, AuditLogger logger, FraudDetectionClient fraudClient) {
        this.gateway = gateway;
        this.notifier = notifier;
        this.logger = logger;
        this.fraudClient = fraudClient;
    }

    public PaymentResponse processPayment(PaymentRequest request) {
        if (request == null) {
            return new PaymentResponse(null, "FAILED", null);
        }

        if (request.getAccountId() == null || request.getAccountId().trim().isEmpty()) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Missing account ID");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_MISSING_ACCOUNT", null);
        }

        if (request.getCurrency() == null || request.getCurrency().length() != 3) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Invalid ISO currency");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_INVALID_CURRENCY", null);
        }

        if (request.getAmount() == null || request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            logger.logTransaction(request.getTransactionId(), "INVALID", "Non-positive amount");
            return new PaymentResponse(request.getTransactionId(), "FAILED_INVALID_AMOUNT", null);
        }

        if (fraudClient != null && !fraudClient.evaluateRisk(request.getAccountId(), request.getAmount(), request.getIpAddress())) {
            logger.logSecurityEvent("FRAUD_SUSPECTED", request.getAccountId(), request.getIpAddress());
            notifier.sendAlert("Suspicious transaction blocked", "HIGH");
            return new PaymentResponse(request.getTransactionId(), "BLOCKED_FRAUD", null);
        }

        int maxRetries = 3;
        int attempt = 0;
        boolean authorized = false;
        long delay = 100L;

        while (attempt < maxRetries && !authorized) {
            attempt++;
            try {
                authorized = gateway.authorize(request);
                if (!authorized && attempt < maxRetries) {
                    logger.logTransaction(request.getTransactionId(), "RETRY", "Attempt " + attempt);
                    Thread.sleep(delay);
                    delay = delay * 2;
                }
            } catch (Exception ex) {
                logger.logTransaction(request.getTransactionId(), "ERROR", "Retry error on attempt " + attempt + ": " + ex.getMessage());
                if (attempt >= maxRetries) {
                    return new PaymentResponse(request.getTransactionId(), "GATEWAY_TIMEOUT", null);
                }
            }
        }

        if (authorized) {
            boolean captured = gateway.capture(request.getTransactionId());
            if (captured) {
                PaymentResponse response = new PaymentResponse(request.getTransactionId(), "SUCCESS", "AUTH-" + System.currentTimeMillis());
                notifier.sendReceipt(request, response);
                logger.logTransaction(request.getTransactionId(), "SUCCESS", "Authorized and captured on attempt " + attempt);
                return response;
            } else {
                logger.logTransaction(request.getTransactionId(), "CAPTURE_FAILED", "Auth ok but capture failed");
                return new PaymentResponse(request.getTransactionId(), "CAPTURE_FAILED", null);
            }
        } else {
            logger.logTransaction(request.getTransactionId(), "DECLINED", "Gateway rejected after retries");
            return new PaymentResponse(request.getTransactionId(), "DECLINED", null);
        }
    }
}
"""

# V4 PaymentService: Nested switch-cases, multi-method routing, CurrencyConverter & TaxService
PAYMENT_SERVICE_V4 = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class PaymentService {
    private final PaymentGateway gateway;
    private final NotificationService notifier;
    private final AuditLogger logger;
    private final FraudDetectionClient fraudClient;
    private final CurrencyConverter currencyConverter;
    private final TaxService taxService;

    public PaymentService(PaymentGateway gateway, NotificationService notifier, AuditLogger logger,
                          FraudDetectionClient fraudClient, CurrencyConverter currencyConverter, TaxService taxService) {
        this.gateway = gateway;
        this.notifier = notifier;
        this.logger = logger;
        this.fraudClient = fraudClient;
        this.currencyConverter = currencyConverter;
        this.taxService = taxService;
    }

    public PaymentResponse processPayment(PaymentRequest request) {
        if (request == null) {
            return new PaymentResponse(null, "FAILED", null);
        }

        if (request.getAccountId() == null || request.getAccountId().trim().isEmpty()) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Missing account ID");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_MISSING_ACCOUNT", null);
        }

        if (request.getCurrency() == null || request.getCurrency().length() != 3) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Invalid ISO currency");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_INVALID_CURRENCY", null);
        }

        if (request.getAmount() == null || request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            logger.logTransaction(request.getTransactionId(), "INVALID", "Non-positive amount");
            return new PaymentResponse(request.getTransactionId(), "FAILED_INVALID_AMOUNT", null);
        }

        if (fraudClient != null && !fraudClient.evaluateRisk(request.getAccountId(), request.getAmount(), request.getIpAddress())) {
            logger.logSecurityEvent("FRAUD_SUSPECTED", request.getAccountId(), request.getIpAddress());
            notifier.sendAlert("Suspicious transaction blocked", "HIGH");
            return new PaymentResponse(request.getTransactionId(), "BLOCKED_FRAUD", null);
        }

        BigDecimal finalAmount = request.getAmount();
        if (!"USD".equalsIgnoreCase(request.getCurrency()) && currencyConverter != null) {
            finalAmount = currencyConverter.convert(finalAmount, request.getCurrency(), "USD");
        }

        BigDecimal tax = BigDecimal.ZERO;
        if (taxService != null) {
            if ("US".equalsIgnoreCase(request.getMerchantId())) {
                tax = taxService.calculateTax(finalAmount, "US");
            } else if ("EU".equalsIgnoreCase(request.getMerchantId())) {
                tax = taxService.calculateTax(finalAmount, "EU");
            }
        }
        finalAmount = finalAmount.add(tax);

        String method = request.getPaymentMethod() != null ? request.getPaymentMethod().toUpperCase() : "UNKNOWN";
        boolean methodSupported = false;

        switch (method) {
            case "CREDIT_CARD":
                if (request.getCardToken() == null || request.getCardToken().isEmpty()) {
                    return new PaymentResponse(request.getTransactionId(), "INVALID_CARD_TOKEN", null);
                }
                methodSupported = true;
                break;
            case "DEBIT_CARD":
                if (request.getCardToken() == null) {
                    return new PaymentResponse(request.getTransactionId(), "MISSING_DEBIT_TOKEN", null);
                }
                methodSupported = true;
                break;
            case "PAYPAL":
                if (request.getAccountId() == null) {
                    return new PaymentResponse(request.getTransactionId(), "INVALID_PAYPAL_ACCOUNT", null);
                }
                methodSupported = true;
                break;
            case "CRYPTO":
                if (request.getAmount().compareTo(new BigDecimal("50000")) > 0) {
                    return new PaymentResponse(request.getTransactionId(), "CRYPTO_LIMIT_EXCEEDED", null);
                }
                methodSupported = true;
                break;
            case "WIRE_TRANSFER":
                if (request.getAmount().compareTo(new BigDecimal("1000")) < 0) {
                    return new PaymentResponse(request.getTransactionId(), "WIRE_MINIMUM_REQUIRED", null);
                }
                methodSupported = true;
                break;
            case "APPLE_PAY":
            case "GOOGLE_PAY":
                methodSupported = true;
                break;
            default:
                logger.logTransaction(request.getTransactionId(), "UNSUPPORTED_METHOD", method);
                return new PaymentResponse(request.getTransactionId(), "UNSUPPORTED_METHOD", null);
        }

        if (!methodSupported) {
            return new PaymentResponse(request.getTransactionId(), "METHOD_REJECTED", null);
        }

        int maxRetries = 3;
        int attempt = 0;
        boolean authorized = false;
        long delay = 100L;

        while (attempt < maxRetries && !authorized) {
            attempt++;
            try {
                authorized = gateway.authorize(request);
                if (!authorized && attempt < maxRetries) {
                    logger.logTransaction(request.getTransactionId(), "RETRY", "Attempt " + attempt);
                    Thread.sleep(delay);
                    delay = delay * 2;
                }
            } catch (Exception ex) {
                logger.logTransaction(request.getTransactionId(), "ERROR", "Retry error: " + ex.getMessage());
                if (attempt >= maxRetries) {
                    return new PaymentResponse(request.getTransactionId(), "GATEWAY_TIMEOUT", null);
                }
            }
        }

        if (authorized) {
            boolean captured = gateway.capture(request.getTransactionId());
            if (captured) {
                PaymentResponse response = new PaymentResponse(request.getTransactionId(), "SUCCESS", "AUTH-" + System.currentTimeMillis());
                notifier.sendReceipt(request, response);
                logger.logTransaction(request.getTransactionId(), "SUCCESS", "Authorized and captured on attempt " + attempt);
                return response;
            } else {
                logger.logTransaction(request.getTransactionId(), "CAPTURE_FAILED", "Auth ok but capture failed");
                return new PaymentResponse(request.getTransactionId(), "CAPTURE_FAILED", null);
            }
        } else {
            logger.logTransaction(request.getTransactionId(), "DECLINED", "Gateway rejected after retries");
            return new PaymentResponse(request.getTransactionId(), "DECLINED", null);
        }
    }
}
"""

# V5 PaymentService: Critical PR with severe monolithic mutation, massive CC, WMC, CBO, high LCOM
PAYMENT_SERVICE_V5 = """package com.evolutionary.payment;

import java.math.BigDecimal;

public class PaymentService {
    private final PaymentGateway gateway;
    private final NotificationService notifier;
    private final AuditLogger logger;
    private final FraudDetectionClient fraudClient;
    private final CurrencyConverter currencyConverter;
    private final TaxService taxService;
    private final TokenVault tokenVault;
    private final LedgerSyncService ledgerSync;

    public PaymentService(PaymentGateway gateway, NotificationService notifier, AuditLogger logger,
                          FraudDetectionClient fraudClient, CurrencyConverter currencyConverter,
                          TaxService taxService, TokenVault tokenVault, LedgerSyncService ledgerSync) {
        this.gateway = gateway;
        this.notifier = notifier;
        this.logger = logger;
        this.fraudClient = fraudClient;
        this.currencyConverter = currencyConverter;
        this.taxService = taxService;
        this.tokenVault = tokenVault;
        this.ledgerSync = ledgerSync;
    }

    public PaymentResponse processPayment(PaymentRequest request) {
        if (request == null) {
            return new PaymentResponse(null, "FAILED_NULL_REQUEST", null);
        }

        if (request.getAccountId() == null || request.getAccountId().trim().isEmpty()) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Missing account ID");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_MISSING_ACCOUNT", null);
        }

        if (request.getCurrency() == null || request.getCurrency().length() != 3) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Invalid ISO currency");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_INVALID_CURRENCY", null);
        }

        if (request.getAmount() == null || request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            logger.logTransaction(request.getTransactionId(), "INVALID", "Non-positive amount");
            return new PaymentResponse(request.getTransactionId(), "FAILED_INVALID_AMOUNT", null);
        }

        if (request.getMerchantId() == null || request.getMerchantId().isEmpty()) {
            logger.logTransaction(request.getTransactionId(), "REJECTED", "Missing merchant ID");
            return new PaymentResponse(request.getTransactionId(), "REJECTED_NO_MERCHANT", null);
        }

        if (fraudClient != null && !fraudClient.evaluateRisk(request.getAccountId(), request.getAmount(), request.getIpAddress())) {
            logger.logSecurityEvent("FRAUD_SUSPECTED", request.getAccountId(), request.getIpAddress());
            notifier.sendAlert("Suspicious transaction blocked", "CRITICAL");
            return new PaymentResponse(request.getTransactionId(), "BLOCKED_FRAUD", null);
        }

        if (tokenVault != null && request.getCardToken() != null && !tokenVault.validateToken(request.getCardToken())) {
            logger.logSecurityEvent("INVALID_VAULT_TOKEN", request.getAccountId(), request.getIpAddress());
            return new PaymentResponse(request.getTransactionId(), "INVALID_VAULT_TOKEN", null);
        }

        BigDecimal finalAmount = request.getAmount();
        if (!"USD".equalsIgnoreCase(request.getCurrency()) && currencyConverter != null) {
            finalAmount = currencyConverter.convert(finalAmount, request.getCurrency(), "USD");
            if (finalAmount == null || finalAmount.compareTo(BigDecimal.ZERO) <= 0) {
                logger.logTransaction(request.getTransactionId(), "CONVERSION_ERROR", "Currency conversion failed");
                return new PaymentResponse(request.getTransactionId(), "CONVERSION_ERROR", null);
            }
        }

        BigDecimal tax = BigDecimal.ZERO;
        if (taxService != null) {
            if ("US".equalsIgnoreCase(request.getMerchantId())) {
                tax = taxService.calculateTax(finalAmount, "US");
            } else if ("EU".equalsIgnoreCase(request.getMerchantId())) {
                tax = taxService.calculateTax(finalAmount, "EU");
            } else if ("APAC".equalsIgnoreCase(request.getMerchantId())) {
                tax = taxService.calculateTax(finalAmount, "APAC");
            } else if ("LATAM".equalsIgnoreCase(request.getMerchantId())) {
                tax = taxService.calculateTax(finalAmount, "LATAM");
            } else {
                tax = taxService.calculateTax(finalAmount, "DEFAULT");
            }
        }
        finalAmount = finalAmount.add(tax);

        String method = request.getPaymentMethod() != null ? request.getPaymentMethod().toUpperCase() : "UNKNOWN";
        boolean methodSupported = false;

        switch (method) {
            case "CREDIT_CARD":
                if (request.getCardToken() == null || request.getCardToken().isEmpty()) {
                    return new PaymentResponse(request.getTransactionId(), "INVALID_CARD_TOKEN", null);
                }
                if (finalAmount.compareTo(new BigDecimal("100000")) > 0) {
                    return new PaymentResponse(request.getTransactionId(), "CARD_LIMIT_EXCEEDED", null);
                }
                methodSupported = true;
                break;
            case "DEBIT_CARD":
                if (request.getCardToken() == null) {
                    return new PaymentResponse(request.getTransactionId(), "MISSING_DEBIT_TOKEN", null);
                }
                if (finalAmount.compareTo(new BigDecimal("25000")) > 0) {
                    return new PaymentResponse(request.getTransactionId(), "DEBIT_LIMIT_EXCEEDED", null);
                }
                methodSupported = true;
                break;
            case "PAYPAL":
                if (request.getAccountId() == null) {
                    return new PaymentResponse(request.getTransactionId(), "INVALID_PAYPAL_ACCOUNT", null);
                }
                methodSupported = true;
                break;
            case "CRYPTO":
                if (finalAmount.compareTo(new BigDecimal("50000")) > 0) {
                    return new PaymentResponse(request.getTransactionId(), "CRYPTO_LIMIT_EXCEEDED", null);
                }
                methodSupported = true;
                break;
            case "WIRE_TRANSFER":
                if (finalAmount.compareTo(new BigDecimal("1000")) < 0) {
                    return new PaymentResponse(request.getTransactionId(), "WIRE_MINIMUM_REQUIRED", null);
                }
                methodSupported = true;
                break;
            case "KLARNA":
            case "AFTERPAY":
                if (finalAmount.compareTo(new BigDecimal("2000")) > 0) {
                    return new PaymentResponse(request.getTransactionId(), "BNPL_LIMIT_EXCEEDED", null);
                }
                methodSupported = true;
                break;
            case "APPLE_PAY":
            case "GOOGLE_PAY":
                methodSupported = true;
                break;
            default:
                logger.logTransaction(request.getTransactionId(), "UNSUPPORTED_METHOD", method);
                return new PaymentResponse(request.getTransactionId(), "UNSUPPORTED_METHOD", null);
        }

        if (!methodSupported) {
            return new PaymentResponse(request.getTransactionId(), "METHOD_REJECTED", null);
        }

        int maxRetries = 4;
        int attempt = 0;
        boolean authorized = false;
        long delay = 100L;

        while (attempt < maxRetries && !authorized) {
            attempt++;
            try {
                authorized = gateway.authorize(request);
                if (!authorized && attempt < maxRetries) {
                    logger.logTransaction(request.getTransactionId(), "RETRY", "Attempt " + attempt);
                    Thread.sleep(delay);
                    delay = delay * 2;
                }
            } catch (Exception ex) {
                logger.logTransaction(request.getTransactionId(), "ERROR", "Retry error: " + ex.getMessage());
                if (attempt >= maxRetries) {
                    return new PaymentResponse(request.getTransactionId(), "GATEWAY_TIMEOUT", null);
                }
            }
        }

        if (authorized) {
            boolean captured = false;
            try {
                captured = gateway.capture(request.getTransactionId());
            } catch (Exception ex) {
                logger.logTransaction(request.getTransactionId(), "CAPTURE_EXCEPTION", ex.getMessage());
            }

            if (captured) {
                PaymentResponse response = new PaymentResponse(request.getTransactionId(), "SUCCESS", "AUTH-" + System.currentTimeMillis());
                notifier.sendReceipt(request, response);
                logger.logTransaction(request.getTransactionId(), "SUCCESS", "Authorized and captured on attempt " + attempt);
                if (ledgerSync != null) {
                    ledgerSync.recordEntry(request.getAccountId(), "DEBIT", finalAmount.toPlainString());
                }
                return response;
            } else {
                logger.logTransaction(request.getTransactionId(), "CAPTURE_FAILED", "Auth ok but capture failed");
                if (ledgerSync != null) {
                    ledgerSync.recordEntry(request.getAccountId(), "FAILED_CAPTURE", finalAmount.toPlainString());
                }
                return new PaymentResponse(request.getTransactionId(), "CAPTURE_FAILED", null);
            }
        } else {
            logger.logTransaction(request.getTransactionId(), "DECLINED", "Gateway rejected after retries");
            return new PaymentResponse(request.getTransactionId(), "DECLINED", null);
        }
    }
}
"""

COMMITS_CONFIG = [
    {
        "version_label": "V1",
        "message": "feat: initial clean architecture for payment service",
        "files": {
            "com/evolutionary/payment/PaymentRequest.java": PAYMENT_REQUEST_JAVA,
            "com/evolutionary/payment/PaymentResponse.java": PAYMENT_RESPONSE_JAVA,
            "com/evolutionary/payment/PaymentGateway.java": PAYMENT_GATEWAY_JAVA,
            "com/evolutionary/payment/NotificationService.java": NOTIFICATION_SERVICE_JAVA,
            "com/evolutionary/payment/AuditLogger.java": AUDIT_LOGGER_JAVA,
            "com/evolutionary/payment/PaymentService.java": PAYMENT_SERVICE_V1,
        },
    },
    {
        "version_label": "V2",
        "message": "feat: add comprehensive request validations to payment processing",
        "files": {
            "com/evolutionary/payment/PaymentService.java": PAYMENT_SERVICE_V2,
        },
    },
    {
        "version_label": "V3",
        "message": "refactor: introduce retry policies, backoff and fraud checks",
        "files": {
            "com/evolutionary/payment/FraudDetectionClient.java": FRAUD_DETECTION_JAVA,
            "com/evolutionary/payment/PaymentService.java": PAYMENT_SERVICE_V3,
        },
    },
    {
        "version_label": "V4",
        "message": "feat: multi-channel routing, currency conversions and tax calculation",
        "files": {
            "com/evolutionary/payment/CurrencyConverter.java": CURRENCY_CONVERTER_JAVA,
            "com/evolutionary/payment/TaxService.java": TAX_SERVICE_JAVA,
            "com/evolutionary/payment/PaymentService.java": PAYMENT_SERVICE_V4,
        },
    },
    {
        "version_label": "V5",
        "message": "feat(pr#142): critical PR adding token vault, BNPL channels, and ledger sync",
        "files": {
            "com/evolutionary/payment/TokenVault.java": TOKEN_VAULT_JAVA,
            "com/evolutionary/payment/LedgerSyncService.java": LEDGER_SYNC_JAVA,
            "com/evolutionary/payment/PaymentService.java": PAYMENT_SERVICE_V5,
        },
    },
]


def generate_mock_repository(target_dir: Path = MOCK_REPO_DIR) -> git.Repo:
    """
    Creates a real local Git repository on disk with 5 realistic commits.
    """
    target_dir = Path(target_dir).resolve()
    
    if target_dir.exists():
        logger.info(f"Removing existing mock repository at: {target_dir}")
        shutil.rmtree(target_dir, ignore_errors=True)

    target_dir.mkdir(parents=True, exist_ok=True)
    src_dir = target_dir / "src" / "main" / "java"
    src_dir.mkdir(parents=True, exist_ok=True)

    repo = git.Repo.init(target_dir)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Software DNA Agent")
        config.set_value("user", "email", "dna-agent@evolutionary.ai")

    for commit_data in COMMITS_CONFIG:
        v_label = commit_data["version_label"]
        msg = commit_data["message"]
        files = commit_data["files"]

        for rel_path, content in files.items():
            full_file_path = src_dir / rel_path
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(content)

        repo.git.add(A=True)
        repo.index.commit(f"[{v_label}] {msg}")
        logger.info(f"Created real Git commit for {v_label}: {msg}")

    logger.info(f"Successfully generated 5-commit mock repository at {target_dir}")
    return repo


if __name__ == "__main__":
    generate_mock_repository()
