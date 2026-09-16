package pl.smarthotel.pms.common.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.MappedSuperclass;
import jakarta.persistence.Version;

/**
 * Audited entity with optimistic locking ({@code version} column). Used by
 * {@code reservations} and any other concurrently updated aggregate.
 */
@MappedSuperclass
public abstract class VersionedAuditedEntity extends AuditedEntity {

    @Version
    @Column(name = "version", nullable = false)
    private long version;

    public long getVersion() {
        return version;
    }
}
