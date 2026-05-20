package go_stub

import (
	"context"
)

// ManifestConfig represents the parsed agent.md front-matter config.
type ManifestConfig struct {
	ProtocolVersion   string                 `json:"protocol_version"`
	MinRuntimeVersion string                 `json:"min_runtime_version"`
	Name              string                 `json:"name"`
	Version           string                 `json:"version"`
	Description       string                 `json:"description,omitempty"`
	Tools             []string               `json:"tools"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
}

// SkillMetadata represents a parsed skill contract (.agent/skills/*.md).
type SkillMetadata struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Version     string                 `json:"version"`
	Inputs      map[string]interface{} `json:"inputs,omitempty"`
	Outputs     map[string]interface{} `json:"outputs,omitempty"`
	SafetyNotes []string               `json:"safety_notes,omitempty"`
}

// WorkflowResult represents the outcome of running a multi-step workflow.
type WorkflowResult struct {
	Status  string                 `json:"status"` // "success" or "failure"
	Outputs map[string]interface{} `json:"outputs"`
	Error   string                 `json:"error,omitempty"`
}

// PAPRuntime defines the required methods for a Go-based runtime.
type PAPRuntime interface {
	// LoadManifest parses the YAML front-matter of the agent.md manifest.
	LoadManifest(ctx context.Context, configPath string) (*ManifestConfig, error)

	// ListSkills scans the workspace skills directory and returns all contract metadata.
	ListSkills(ctx context.Context) ([]SkillMetadata, error)

	// CallSkill executes a single skill with the given inputs, returning outputs.
	CallSkill(ctx context.Context, skillID string, params map[string]interface{}) (map[string]interface{}, error)

	// ReadMemory reads a key-value record from persistent storage.
	ReadMemory(ctx context.Context, key string) (interface{}, error)

	// WriteMemory persists a key-value record to storage.
	WriteMemory(ctx context.Context, key string, value interface{}) (bool, error)

	// RunWorkflow executes a multi-step workflow topology.
	RunWorkflow(ctx context.Context, workflowID string, params map[string]interface{}) (*WorkflowResult, error)
}
