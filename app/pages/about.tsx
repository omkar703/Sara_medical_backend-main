import React from 'react';
import { Container, Typography, Box, Paper, Grid, Card, CardContent } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import SecurityIcon from '@mui/icons-material/Security';
import MedicationIcon from '@mui/icons-material/Medication';
import PeopleIcon from '@mui/icons-material/People';

const AboutPage: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 8 }}>
      {/* Header Section */}
      <Box sx={{ mb: 6, textAlign: 'center' }}>
        <Typography variant="h2" component="h1" sx={{ mb: 2, fontWeight: 'bold', color: '#2563EB' }}>
          About SaraMedico
        </Typography>
        <Typography variant="h6" sx={{ color: '#666', mb: 4 }}>
          HIPAA-Compliant Medical AI Platform
        </Typography>
      </Box>

      {/* Main Description */}
      <Paper sx={{ p: 4, mb: 6, backgroundColor: '#F0F9FF', borderLeft: '4px solid #2563EB' }}>
        <Typography variant="body1" sx={{ fontSize: '1.1rem', lineHeight: 1.8, color: '#333' }}>
          SaraMedico is a comprehensive healthcare management platform designed to streamline patient care, 
          clinical documentation, and AI-powered medical insights. Built with security and compliance at its core, 
          SaraMedico empowers healthcare providers to deliver better patient outcomes through intelligent automation 
          and secure data management.
        </Typography>
      </Paper>

      {/* Company Info Grid */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', boxShadow: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MedicationIcon sx={{ fontSize: 40, color: '#2563EB', mr: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Healthcare
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Specializing in medical technology and patient management solutions
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', boxShadow: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon sx={{ fontSize: 40, color: '#2563EB', mr: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Secure
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                HIPAA-compliant with enterprise-grade security and data protection
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', boxShadow: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <InfoIcon sx={{ fontSize: 40, color: '#2563EB', mr: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  AI-Powered
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Advanced AI for document analysis and clinical insights
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', boxShadow: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PeopleIcon sx={{ fontSize: 40, color: '#2563EB', mr: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Collaborative
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Multi-role support for doctors, patients, and administrators
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Features Section */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold', color: '#333' }}>
          Key Features
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>Patient Management:</strong> Comprehensive patient records and medical history
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>AI-Powered Analysis:</strong> Claude-based document processing and insights
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>Secure Messaging:</strong> HIPAA-compliant communication channels
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>Multi-factor Authentication:</strong> Enhanced account security
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>Appointment Scheduling:</strong> Integrated calendar management
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>Document Management:</strong> Secure file storage and organization
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>Audit Logging:</strong> Complete compliance and accountability tracking
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              ✓ <strong>Role-Based Access:</strong> Granular permission controls
            </Typography>
          </Grid>
        </Grid>
      </Box>

      {/* Privacy & Compliance */}
      <Paper sx={{ p: 4, backgroundColor: '#FEF3C7', borderLeft: '4px solid #F59E0B' }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#92400E' }}>
          Privacy & Compliance
        </Typography>
        <Typography variant="body1" sx={{ mb: 2, color: '#333' }}>
          SaraMedico is committed to protecting your privacy and maintaining the highest standards of data security:
        </Typography>
        <Typography variant="body2" sx={{ mb: 1, color: '#333' }}>
          • <strong>HIPAA Compliance:</strong> Full compliance with Health Insurance Portability and Accountability Act
        </Typography>
        <Typography variant="body2" sx={{ mb: 1, color: '#333' }}>
          • <strong>End-to-End Encryption:</strong> PII encrypted at rest and in transit
        </Typography>
        <Typography variant="body2" sx={{ mb: 1, color: '#333' }}>
          • <strong>AI Processing Disclosure:</strong> Transparent disclosure of AI providers and data processing
        </Typography>
        <Typography variant="body2" sx={{ mb: 1, color: '#333' }}>
          • <strong>User Consent:</strong> Explicit opt-in required for AI processing of sensitive health data
        </Typography>
        <Typography variant="body2" sx={{ color: '#333' }}>
          • <strong>Audit Trail:</strong> Complete logs of all data access and modifications
        </Typography>
      </Paper>

      {/* Footer Info */}
      <Box sx={{ mt: 6, pt: 4, borderTop: '2px solid #E5E7EB', textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          For more information, please visit our{' '}
          <a href="/privacy" style={{ color: '#2563EB', textDecoration: 'none' }}>
            Privacy Policy
          </a>
          {' '}or{' '}
          <a href="/terms" style={{ color: '#2563EB', textDecoration: 'none' }}>
            Terms of Service
          </a>
          .
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
          © {new Date().getFullYear()} SaraMedico. All rights reserved.
        </Typography>
      </Box>
    </Container>
  );
};

export default AboutPage;
