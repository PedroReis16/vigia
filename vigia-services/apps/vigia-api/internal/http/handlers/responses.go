package handlers

// MessageResponse é o corpo padrão para respostas que retornam apenas uma mensagem.
type MessageResponse struct {
	Message string `json:"message"`
}

// ErrorResponse é o corpo padrão para respostas de erro retornadas pela API.
type ErrorResponse struct {
	Error string `json:"error"`
}
