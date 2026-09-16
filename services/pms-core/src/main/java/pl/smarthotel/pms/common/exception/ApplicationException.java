package pl.smarthotel.pms.common.exception;

import org.springframework.http.HttpStatus;
import pl.smarthotel.pms.common.web.ProblemTypes;

/**
 * Base for domain/API errors that map cleanly to RFC 7807 ProblemDetail.
 */
public abstract class ApplicationException extends RuntimeException {

    private final String problemType;
    private final HttpStatus status;
    private final String title;

    protected ApplicationException(
            String problemType, HttpStatus status, String title, String detail) {
        super(detail);
        this.problemType = problemType;
        this.status = status;
        this.title = title;
    }

    public String getProblemType() {
        return problemType;
    }

    public HttpStatus getStatus() {
        return status;
    }

    public String getTitle() {
        return title;
    }

    public static NotFoundException notFound(String detail) {
        return new NotFoundException(detail);
    }

    public static ConflictException conflict(String detail) {
        return new ConflictException(ProblemTypes.CONFLICT, "Conflict", detail);
    }

    public static BadRequestException badRequest(String detail) {
        return new BadRequestException(detail);
    }

    public static final class NotFoundException extends ApplicationException {
        public NotFoundException(String detail) {
            super(ProblemTypes.NOT_FOUND, HttpStatus.NOT_FOUND, "Not found", detail);
        }
    }

    public static final class ConflictException extends ApplicationException {
        public ConflictException(String problemType, String title, String detail) {
            super(problemType, HttpStatus.CONFLICT, title, detail);
        }
    }

    public static final class BadRequestException extends ApplicationException {
        public BadRequestException(String detail) {
            super(ProblemTypes.VALIDATION_ERROR, HttpStatus.BAD_REQUEST, "Validation failed", detail);
        }
    }
}
