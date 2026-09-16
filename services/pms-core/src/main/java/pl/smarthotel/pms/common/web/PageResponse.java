package pl.smarthotel.pms.common.web;

import java.util.List;
import org.springframework.data.domain.Page;

/**
 * Cursor-less page wrapper used by list endpoints ({@code ?page=&size=}).
 */
public record PageResponse<T>(List<T> content, PageMeta page) {

    public static <T> PageResponse<T> from(Page<T> page) {
        return new PageResponse<>(
                page.getContent(),
                new PageMeta(
                        page.getNumber(),
                        page.getSize(),
                        page.getTotalElements(),
                        page.getTotalPages()));
    }

    public record PageMeta(int number, int size, long totalElements, int totalPages) {}
}
