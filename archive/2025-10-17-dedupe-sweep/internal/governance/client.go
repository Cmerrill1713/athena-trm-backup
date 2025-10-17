package governance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"go.uber.org/zap"
)

// Client handles communication with the governance orchestrator
type Client struct {
	url    string
	logger *zap.Logger
	client *http.Client
}

// NewClient creates a new governance client
func NewClient(url string, logger *zap.Logger) *Client {
	return &Client{
		url:    url,
		logger: logger,
		client: &http.Client{
			Timeout: 5 * time.Second,
		},
	}
}

// CheckApproval checks if an action requires governance approval
func (c *Client) CheckApproval(action string, backend string) (bool, error) {
	req := map[string]interface{}{
		"action":  action,
		"backend": backend,
	}

	data, err := json.Marshal(req)
	if err != nil {
		return false, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.client.Post(c.url+"/check_approval", "application/json", bytes.NewReader(data))
	if err != nil {
		c.logger.Warn("Failed to check governance approval", zap.Error(err))
		return false, nil // Fail open
	}
	defer resp.Body.Close()

	var result struct {
		Approved bool `json:"approved"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false, fmt.Errorf("failed to decode response: %w", err)
	}

	return result.Approved, nil
}

// LogDecision logs a routing decision to the governance system
func (c *Client) LogDecision(decision map[string]interface{}) error {
	data, err := json.Marshal(decision)
	if err != nil {
		return fmt.Errorf("failed to marshal decision: %w", err)
	}

	resp, err := c.client.Post(c.url+"/log_decision", "application/json", bytes.NewReader(data))
	if err != nil {
		c.logger.Warn("Failed to log decision", zap.Error(err))
		return err
	}
	defer resp.Body.Close()

	return nil
}
