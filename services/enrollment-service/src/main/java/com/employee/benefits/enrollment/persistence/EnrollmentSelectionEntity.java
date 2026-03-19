package com.employee.benefits.enrollment.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "enrollment_selection", schema = "enrollment")
public class EnrollmentSelectionEntity {

    @Id
    @Column(name = "selection_id", nullable = false, length = 64)
    private String selectionId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "enrollment_id", nullable = false)
    private EnrollmentRecordEntity enrollment;

    @Column(name = "benefit_type", nullable = false, length = 100)
    private String benefitType;

    @Column(name = "benefit_plan", nullable = false, length = 100)
    private String benefitPlan;

    public String getSelectionId() {
        return selectionId;
    }

    public void setSelectionId(String selectionId) {
        this.selectionId = selectionId;
    }

    public EnrollmentRecordEntity getEnrollment() {
        return enrollment;
    }

    public void setEnrollment(EnrollmentRecordEntity enrollment) {
        this.enrollment = enrollment;
    }

    public String getBenefitType() {
        return benefitType;
    }

    public void setBenefitType(String benefitType) {
        this.benefitType = benefitType;
    }

    public String getBenefitPlan() {
        return benefitPlan;
    }

    public void setBenefitPlan(String benefitPlan) {
        this.benefitPlan = benefitPlan;
    }
}
